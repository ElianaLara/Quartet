from flask import current_app, session
from bson import ObjectId


def get_user_by_id(user_id):
    """Fetch full user document from an ObjectId or string ID."""
    db = current_app.db
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.find_one({"_id": user_id})


def parse_non_negotiables(non_negotiables_str):
    """
    Parse non_negotiables string into a set of keyword strings.
    e.g. "politics:conservative,religion:christian" -> {"politics:conservative", "religion:christian"}
    """
    result = set()
    if not non_negotiables_str:
        return result
    for part in non_negotiables_str.split(","):
        part = part.strip().lower()
        if ":" in part:
            result.add(part)
    return result


def get_user_keywords_set(user):
    """
    Get all keywords for a user as a set of strings like "politics:conservative".
    Fetches from messages collection.
    """
    db = current_app.db
    messages = db.messages.find({"user_email": user.get("email")})
    keywords = set()
    for msg in messages:
        raw = msg.get("keywords", "0")
        if not raw or raw.strip() == "0":
            continue
        for part in raw.split(","):
            part = part.strip().lower()
            if ":" in part:
                keywords.add(part)
    return keywords


def passes_blacklist(candidate, my_non_negotiables):
    """
    Returns True if candidate does not have any keywords in my blacklist.
    """
    if not my_non_negotiables:
        return True

    candidate_keywords = get_user_keywords_set(candidate)
    if candidate_keywords & my_non_negotiables:
        return False

    return True


def passes_availability(candidate, my_availability):
    """
    Returns True if candidate shares at least one availability slot with me.
    """
    if not my_availability:
        return True  # if I have no availability set, don't filter

    candidate_availability = set(candidate.get("availability") or [])
    my_availability_set = set(my_availability)

    return bool(candidate_availability & my_availability_set)


def passes_filters(candidate, me):
    """
    Returns True only if candidate passes both blacklist and availability filters.
    """
    my_non_negotiables = parse_non_negotiables(me.get("non_negotiables", ""))
    my_availability = me.get("availability", [])

    if not passes_blacklist(candidate, my_non_negotiables):
        print(f"  Blacklist filter failed for {candidate.get('email')}")
        return False

    if not passes_availability(candidate, my_availability):
        print(f"  Availability filter failed for {candidate.get('email')}")
        return False

    return True


def form_group():
    """
    Build a group of 4 starting from the logged-in user's buddies.
    Filters out anyone who fails blacklist or availability checks.
    Expands to buddies-of-buddies if not enough valid candidates found.
    Returns a list of up to 4 user IDs.
    """
    db = current_app.db

    user_email = session.get("user_email")
    me = db.users.find_one({"email": user_email})
    if not me:
        return []

    my_id = me["_id"]
    group = [my_id]
    visited = {str(my_id)}
    queue = _get_buddy_ids(me, visited)

    while len(group) < 4 and queue:
        candidate_id = queue.pop(0)
        candidate = get_user_by_id(candidate_id)
        if not candidate:
            continue

        visited.add(str(candidate_id))

        if passes_filters(candidate, me):
            group.append(candidate_id)
            print(f"  Added {candidate.get('email')} to group ({len(group)}/4)")
        else:
            print(f"  Skipped {candidate.get('email')} — failed filters")

        # always expand their buddies regardless of whether they passed
        # so we can find valid candidates deeper in the network
        if len(group) < 4:
            queue.extend(_get_buddy_ids(candidate, visited))

    print(f"Group formed with {len(group)} members.")
    return group


def _get_buddy_ids(user, visited):
    """
    Return a list of unvisited buddy IDs from a user document.
    """
    buddies_raw = user.get("buddies", {})
    result = []
    for key in sorted(buddies_raw.keys()):
        raw_id = buddies_raw[key]
        try:
            oid = ObjectId(raw_id) if isinstance(raw_id, str) else raw_id
            if str(oid) not in visited:
                result.append(oid)
        except Exception:
            continue
    return result


def save_group(group):
    """
    Write the group to the groups collection.
    Returns the inserted group's _id or None if group is too small.
    """
    db = current_app.db
    if len(group) < 2:
        return None

    group_doc = {
        "members": [str(uid) for uid in group],
        "size": len(group)
    }
    result = db["groups"].insert_one(group_doc)
    return result.inserted_id


def form_and_save_group():
    """
    Form a filtered group and save it to the database.
    Returns the new group's MongoDB ID, or None if formation failed.
    """
    group = form_group()
    if not group:
        return None
    return save_group(group)


def get_group_members(group_id):
    """
    Fetch full user documents for every member of a saved group.
    """
    db = current_app.db
    if isinstance(group_id, str):
        group_id = ObjectId(group_id)

    group_doc = db["groups"].find_one({"_id": group_id})
    if not group_doc:
        return []

    members = []
    for uid_str in group_doc.get("members", []):
        user = get_user_by_id(uid_str)
        if user:
            members.append(user)
    return members