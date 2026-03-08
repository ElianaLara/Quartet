#to calculate what bucket(s) a new user goes into
from flask import current_app, session
import pymongo

def calculate_bucket(): #pass in the user?
    db = current_app.db
    bucket_table = db["bucket"] #inside "" put name of bucket table
    user_score = 0
    user = "" #how am I getting user info?????!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! as soon as user entered to database call this maybe?
    for bucket in bucket_table.find():
        if user["hobbies"] == bucket["hobbies"]:
            user_score += 3
        if user["music"] == bucket["music"]:
            user_score += 3
        if user["education"] == bucket["education"]:
            user_score += 2
        if user["politics"] == bucket["politics"]:
            user_score += 2
        if user["languages"] == bucket["languages"]:
            user_score += 1
        if user["religion"] == bucket["religion"]:
            user_score += 1

        if confirm_match(user_score):
            dict = {
                "username": user["username"], #make sure field name matched actually
                "bucket_id": bucket["_id"] #make sure field name matched actually
            }
            bucket_user_table = db["bucket_users"] #inside "" put name of bucket user link table
            bucket_user_table.insert_one(dict) #writes new line of table that links user to a bucket

#to confirm whether a score is high enough to form a match
def confirm_match(score):
    if score >= 5: #number might change
        return True
    else:
        return False

def pick_bucket(user):
    pass

    #list of buckets the user is part of
    #randomly pick one from 0 to len list
    #match_group(user)


#to create a group of four matching people
def match_group(user): #maybe pass what bucket you want to match in when a user presses the button
    db = current_app.db
    non_negotiable_table = db["non_negotiable"] #inside "" put name of group table
    group_table = db["group"] #inside "" put name of group table

    new_group_list = []
    finished = False

    user = "" #pick a random user from the bucket !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    new_group_list.append(user)

    while not finished:
        add_to_group = True
        temp_user = "" #pick a random user who is in the bucket specified !!!!!!!!!!!!!!!!!!!!!!!1!!!

        #for user in new_group_list:
            #if temp_user has a characteristic that is in user non negotiables table:
                # add_to_group = False
        #if add_to_group:
            #new_group_list.append(temp_user)

        if len(new_group_list) == 4:
            finished = True

    #group_table.insert_one(db) #write group to the database (table of groups) #mightb need it in a for loop

def jenna_to_document(jenna_str):
    doc = {}
    parts = jenna_str.split(",")

    for part in parts:
        topic, choice = part.lstrip("+").split(":")
    if topic in doc:
        doc[topic].append(choice)
    else:
        doc[topic] = [choice]

    return doc


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
    steps = 50
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