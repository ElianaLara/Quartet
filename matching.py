#to calculate what bucket(s) a new user goes into
def calculate_bucket(): #pass in the user
    pass
    #user_score = 0
    #for all buckets:
        #if user.hobbies == bucket.hobbies:
            #user_score += 3
        #if user.music == bucket.hobbies:
            #user_score += 3
        #if user.education == bucket.education:
            #user_score += 2
        #if user.politics == bucket.education:
            #user_score += 2
        #if user.languages == bucket.education:
            #user_score += 1
        #if user.religion == bucket.religion:
            #user_score += 1


        #if confirm_match():
            #write new line of table that links user to a bucket

#to confirm whether a score is high enough to form a match
def confirm_match(score):
    if score >= 5: #number might change
        return True
    else:
        return False

def match_group(): #maybe pass what bucket you want to match in
    pass
    #group_list = []
    #finished = False

    #user = pick a random user from the bucket
    #group_list.append(user)

    #while not finished:
        #add_to_group = True
        #temp_user = pick a random user who is in the bucket specified

        #for user in group_list:
            #if temp_user has a characteristic that is in user non negotiables table:
                # add_to_group = False
        #if add_to_group:
            #group_list.append(temp_user)

        #if len(group_list) == 4:
            #finished = True

    #write group to the database (table of groups)
