from flask import current_app, session
#arguments it needs are the keyword strings for both users and both user IDs
#I have called it ID throughout this but the field from the database is user_name
def calculate_match_score(data_str_one, data_str_two, ID_1, ID_2):
    dict_user_one = make_keywords_dictionary(data_str_one)
    dict_user_two = make_keywords_dictionary(data_str_two)
    user_score = 0

    weights = {
        "hobbies": 3,
        "music": 3,
        "education": 2,
        "politics": 2,
        "languages": 1,
        "religion": 1
    }

    for key in dict_user_one.keys() & dict_user_two.keys():
        list_one = dict_user_one[key]
        list_two = dict_user_two[key]
        if set(list_one) & set(list_two): #if they share values
            user_score += weights.get(key, 0)
    return (ID_1, ID_2, user_score)


def make_keywords_dictionary(data_str):
    result = {}
    if not data_str or data_str.strip() == "0":
        return result
    for part in data_str.split(","):
        if ":" not in part:
            continue  # skip malformed entries
        key, value = part.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            if key in result:
                result[key].append(value)
            else:
                result[key] = [value]
    return result

from flask import current_app

def random_user():
    db = current_app.db
    result = list(db.users.aggregate([{"$sample": {"size": 1}}]))
    if result:
        return result[0]["_id"]
    return None

def search():
    db = current_app.db
    buddies = 10
    steps = 10
    buddy_dict = {}
    for i in range(buddies):
        bestUser = random_user()
        for j in range(steps):
            bestUser = findBest(bestUser)
        buddy_dict[str(i)] = bestUser

    user_id = get_id_from_email(session.get("user_email"))
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"buddies": buddy_dict}}
    )

def get_user_keywords(user_id):
    db = current_app.db
    user = db.users.find_one({"_id": user_id})
    if not user:
        return []
    messages = db.messages.find({"user_email": user.get("email")})  # was user_name
    return [msg["keywords"] for msg in messages if msg.get("keywords")]


def findBest(other_id):
    db = current_app.db
    my_id = get_id_from_email(session.get("user_email"))
    my_keywords = ",".join(get_user_keywords(my_id))

    other_user = db.users.find_one({"_id": other_id})
    if not other_user:
        return other_id

    # if they have no buddies yet, just score them directly and return
    if not other_user.get("buddies"):
        return other_id

    other_keywords = ",".join(get_user_keywords(other_id))
    _, __, best_score = calculate_match_score(my_keywords, other_keywords, my_id, other_id)
    best_id = other_id

    for key, buddy_id in other_user.get("buddies", {}).items():
        buddy_keywords = ",".join(get_user_keywords(buddy_id))
        _, __, score = calculate_match_score(my_keywords, buddy_keywords, my_id, buddy_id)
        if score > best_score:
            best_score = score
            best_id = buddy_id

    return best_id#

def findBest_for_user(other_id, my_id):
    """Same as findBest but takes my_id directly instead of reading from session."""
    db = current_app.db
    my_keywords = ",".join(get_user_keywords(my_id))

    other_user = db.users.find_one({"_id": other_id})
    if not other_user or not other_user.get("buddies"):
        return other_id

    other_keywords = ",".join(get_user_keywords(other_id))
    _, __, best_score = calculate_match_score(my_keywords, other_keywords, my_id, other_id)
    best_id = other_id

    for key, buddy_id in other_user.get("buddies", {}).items():
        buddy_keywords = ",".join(get_user_keywords(buddy_id))
        _, __, score = calculate_match_score(my_keywords, buddy_keywords, my_id, buddy_id)
        if score > best_score:
            best_score = score
            best_id = buddy_id

    return best_id

def get_id_from_email(email):
    db = current_app.db
    user = db.users.find_one({"email": email}, {"_id": 1})  # only fetch _id field
    return user["_id"] if user else None