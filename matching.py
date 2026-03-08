#to calculate what bucket(s) a new user goes into
from flask import current_app

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




def calculate_match_score(user_one, user_two):
    user_score = 0
    if user_one["hobbies"] == user_two["hobbies"]:
        user_score += 3
    if user_one["music"] == user_two["music"]:
        user_score += 3
    if user_one["education"] == user_two["education"]:
        user_score += 2
    if user_one["politics"] == user_two["politics"]:
        user_score += 2
    if user_one["languages"] == user_two["languages"]:
        user_score += 1
    if user_one["religion"] == user_two["religion"]:
        user_score += 1