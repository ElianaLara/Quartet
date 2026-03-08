from flask import current_app, session
from bson import ObjectId


def get_user_by_id(user_id):
    """Fetch full user document from an ObjectId or string ID."""
    db = current_app.db
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    return db.users.find_one({"_id": user_id})


def form_group():
    """
    Build a group of 4 starting from the logged-in user's buddies.
    If buddies aren't enough, expand to buddies-of-buddies and so on.
    Returns a list of 4 user IDs, or as many as could be found.
    """
    db = current_app.db

    user_email = session.get("user_email")
    me = db.users.find_one({"email": user_email})
    if not me:
        return []

    my_id = me["_id"]
    group = [my_id]                      # start with ourselves
    visited = {str(my_id)}               # track who we've already seen
    queue = _get_buddy_ids(me, visited)  # seed queue with our direct buddies

    while len(group) < 4 and queue:
        candidate_id = queue.pop(0)
        candidate = get_user_by_id(candidate_id)
        if not candidate:
            continue

        group.append(candidate_id)
        visited.add(str(candidate_id))

        # if we still need more people, add this person's buddies to the queue
        if len(group) < 4:
            queue.extend(_get_buddy_ids(candidate, visited))

    return group


def _get_buddy_ids(user, visited):
    """
    Return a list of buddy IDs from a user doc that haven't been visited yet.
    Handles buddies stored as ObjectId or string.
    """
    buddies_raw = user.get("buddies", {})
    result = []
    for key in sorted(buddies_raw.keys()):  # sorted for deterministic order
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
    Write the group of 4 to the groups collection.
    Stores member IDs as strings for easy retrieval.
    """
    db = current_app.db
    if len(group) < 2:
        return None  # don't save a group of 1

    group_doc = {
        "members": [str(uid) for uid in group],
        "size": len(group)
    }
    result = db["groups"].insert_one(group_doc)
    return result.inserted_id


def form_and_save_group():
    """
    Convenience function: form a group and save it to the database.
    Returns the new group's MongoDB ID, or None if formation failed.
    """
    group = form_group()
    if not group:
        return None
    return save_group(group)


def get_group_members(group_id):
    """
    Fetch full user documents for every member of a saved group.
    Pass in the group's MongoDB _id (string or ObjectId).
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