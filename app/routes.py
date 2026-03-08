from flask import render_template, redirect, url_for, session, Blueprint, flash, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from group_formation import form_and_save_group, get_group_members
from .forms import LoginForm, RegisterForm, ProfileForm
from Chatbot import intro, send_answer, extract_keywords
from matching import calculate_match_score, get_user_keywords, get_id_from_email, search, findBest_for_user
from threading import Thread

main = Blueprint("main", __name__)

chat_messages = []


@main.route("/setup-admin")
def setup_admin():
    db = current_app.db

    # only create if doesn't already exist
    if db.users.find_one({"email": "admin@test.com"}):
        return "Admin already exists"

    db.users.insert_one({
        "email": "admin@test.com",
        "password": generate_password_hash("Admin123!"),
        "name": "Admin",
        "phone": "07000000000",
        "age": 25,
        "gender": "Other",
        "location": "London",
        "non_negotiables": ""
    })
    return "Admin created"

@main.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db = current_app.db

        # Find the user by email
        user = db.users.find_one({"email": form.email.data})

        if user:
            # NOTE: For production, hash passwords instead of plaintext
            if check_password_hash(user["password"], form.password.data):
                # Login successful
                session['user_email'] = user['email']
                session['user_name'] = user.get('name', user['email'])
                flash("Login successful!", "success")

                # Redirect to profile if no profile data, else dashboard
                if not user.get('name') and not user.get('non_negotiables'):
                    return redirect(url_for("main.profile"))
                else:
                    return redirect(url_for("main.dashboard"))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("User not found.", "error")

    return render_template("start.html", form=form)


@main.route("/profile", methods=["GET", "POST"])
def profile():
    db = current_app.db

    # Ensure user is logged in
    user_email = session.get('user_email')
    if not user_email:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    # Fetch user
    user = db.users.find_one({"email": user_email})

    # Initialize form with current user data
    form = ProfileForm(
        name=user.get("name", ""),
        email=user.get("email", ""),
        phone=user.get("phone", ""),
        age=user.get("age", ""),
        gender=user.get("gender", ""),
        location=user.get("location", ""),
        non_negotiables=user.get("non_negotiables", ""),
        availability = user.get("availability", "")
    )

    if form.validate_on_submit():
        updated_data = {
            "name": form.name.data,
            "email": form.email.data,
            "phone": form.phone.data,
            "age": form.age.data,
            "gender": form.gender.data,
            "non_negotiables": form.non_negotiables.data,
            "location": form.location.data,
            "availability": form.availability.data
        }

        # Update password if provided
        if form.password.data:
            updated_data["password"] = form.password.data

        db.users.update_one({"email": user_email}, {"$set": updated_data})

        # Update session if email changed
        session['user_email'] = updated_data["email"]
        session['user_name'] = updated_data.get("name", updated_data["email"])

        flash("Profile updated successfully!", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html", form=form, user=user)



@main.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    return render_template('dashboard.html')

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db = current_app.db  # safe reference to database

        # check if email exists
        if db.users.find_one({"email": form.email.data}):
            flash("Email already registered.", "error")
            return redirect(url_for("main.register"))

        user_data = {
            "email": form.email.data,
            "password": generate_password_hash(form.password.data),
            "phone": form.phone.data,
            "age": form.age.data,
            "gender": form.gender.data,
            "location": form.location.data
        }

        result = db.users.insert_one(user_data)
        print("Inserted ID:", result.inserted_id)  # debug


        flash("Registration successful!", "success")
        return redirect(url_for("main.register"))

    return render_template("register.html", form=form)

@main.route("/chat")
def chat():
    # Ensure user is logged in
    if "user_email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    chat_messages.append({
        "sender": session.get("Jenna"),
        "text": intro()
    })

    # Serve the chat HTML page
    return render_template("chat.html")

@main.route("/send_message", methods=["POST"])
def send_message():
    db = current_app.db
    data = request.json
    text = data.get("message", "").strip()
    if not text:
        return {"status": "error", "message": "Empty message"}, 400

    user_email = session.get("user_email", "Anonymous")
    user_name = session.get("user_name", "You")

    # Extract keywords from message
    keywords = extract_keywords(text)
    db.messages.insert_one({"user_email": user_email, "keywords": keywords})

    chat_messages.append({"sender": user_email, "text": text})
    chat_messages.append({"sender": "Jenna", "text": send_answer(text)})
    chat_messages.append({"sender": "Extracted", "text": keywords, "hidden": True})

    # update buddies after every message
    try:
        search()
    except Exception as e:
        print("Search failed:", e)  # don't crash the chat if search fails

    return {"status": "success"}


@main.route("/get_messages")
def get_messages():
    return {"messages": chat_messages}


@main.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user_email", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))

@main.route("/my_keywords")
def my_keywords():
    db = current_app.db
    user_name = session.get("user_name")

    if not user_name:
        flash("Please log in first to see your keywords.", "error")
        return redirect(url_for("main.login"))

    # Fetch all messages for this user
    messages = db.messages.find({"user_name": user_name})
    keywords_list = []

    for msg in messages:
        kw = msg.get("keywords")
        if kw:
            keywords_list.append(kw)

    if not keywords_list:
        flash("No keywords found for you yet.", "info")
        keywords_list = []


    # Option 2: Show in browser (simple HTML page)
    return render_template("plus.html", keywords=keywords_list, user_name=user_name)

def parse_keyword_list(keyword_str):
    result = []
    if not keyword_str or keyword_str.strip() == "0":
        return result
    for part in keyword_str.split(","):
        if ":" not in part:
            continue
        category, value = part.split(":", 1)
        result.append({"category": category.strip(), "value": value.strip()})
    return result

import random

@main.route("/add-fake-users")
def add_fake_users():
    db = current_app.db

    first_names = [
        "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah",
        "Ivan", "Julia", "Kevin", "Laura", "Marcus", "Nina", "Oscar", "Paula",
        "Quinn", "Rachel", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xander",
        "Yara", "Zoe", "Liam", "Mia", "Noah", "Ella", "James", "Sophia",
        "Oliver", "Ava", "Elijah", "Isabella", "Lucas", "Mila", "Mason", "Aria",
        "Logan", "Chloe", "Aiden", "Penelope", "Jackson", "Layla", "Sebastian",
        "Riley", "Mateo", "Zoey", "Jack", "Nora", "Owen", "Lily", "Theodore",
        "Eleanor", "Caleb", "Hannah", "Ryan", "Lillian", "Nathan", "Addison",
        "Dylan", "Aubrey", "Aaron", "Ellie", "Connor", "Stella", "Evan", "Natalie",
        "Ravi", "Priya", "Arjun", "Ananya", "Mohammed", "Fatima", "Omar", "Yasmin",
        "Chen", "Wei", "Hiroshi", "Yuki", "Santiago", "Valentina", "Andrei", "Ioana",
        "Kwame", "Amara", "Tariq", "Leila", "Dmitri", "Natasha", "Finn", "Aoife"
    ]

    last_names = [
        "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Evans",
        "Wilson", "Thomas", "Roberts", "Johnson", "Walker", "Wright", "Robinson",
        "Thompson", "White", "Hughes", "Edwards", "Green", "Hall", "Lewis",
        "Harris", "Clarke", "Patel", "Jackson", "Wood", "Turner", "Martin",
        "Cooper", "Hill", "Ward", "Morris", "Moore", "Clark", "Lee", "King",
        "Baker", "Harrison", "Morgan", "Allen", "James", "Scott", "Phillips",
        "Watson", "Davis", "Parker", "Price", "Bennett", "Young", "Griffin",
        "Murray", "Stone", "Reid", "Campbell", "Shaw", "Khan", "Singh", "Ali",
        "Ahmed", "Hassan", "Rahman", "Chen", "Wang", "Zhang", "Liu", "Nguyen",
        "Tran", "Garcia", "Martinez", "Rodriguez", "Lopez", "Gonzalez", "Perez",
        "Kowalski", "Novak", "Fischer", "Weber", "Meyer", "Rossi", "Ferrari",
        "Okafor", "Mensah", "Diallo", "Tremblay", "Dubois", "Leblanc", "Murphy"
    ]

    locations = [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool",
        "Bristol", "Edinburgh", "Sheffield", "Newcastle", "Cardiff", "Nottingham",
        "Leicester", "Brighton", "Oxford", "Cambridge", "York", "Bath",
        "Southampton", "Portsmouth", "Reading", "Milton Keynes", "Coventry",
        "Derby", "Wolverhampton", "Plymouth", "Exeter", "Norwich", "Ipswich",
        "Dundee", "Aberdeen", "Inverness", "Swansea", "Belfast", "Derry",
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
        "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Denver",
        "Seattle", "Boston", "Nashville", "Portland", "Las Vegas", "Miami",
        "Toronto", "Vancouver", "Montreal", "Sydney", "Melbourne", "Brisbane",
        "Paris", "Berlin", "Madrid", "Rome", "Amsterdam", "Vienna", "Zurich",
        "Dublin", "Lisbon", "Prague", "Warsaw", "Budapest", "Athens", "Stockholm",
        "Copenhagen", "Oslo", "Helsinki", "Tokyo", "Seoul", "Singapore", "Mumbai",
        "Delhi", "Bangalore", "Dubai", "Cape Town", "Nairobi", "Lagos", "Cairo"
    ]

    genders = ["Male", "Female", "Other"]

    keyword_pools = {
        "hobbies": [
            "hiking", "gaming", "cooking", "reading", "cycling", "swimming",
            "photography", "painting", "gardening", "travelling", "yoga",
            "climbing", "football", "tennis", "running", "surfing", "skateboarding",
            "fishing", "knitting", "dancing", "boxing", "chess", "baking",
            "pottery", "woodworking", "archery", "astronomy", "bird-watching",
            "calligraphy", "candle-making", "caving", "cosplay", "crocheting",
            "diy", "embroidery", "falconry", "foraging", "glassblowing",
            "homebrewing", "horse-riding", "jewellery-making", "kayaking",
            "leatherworking", "lego", "magic", "martial-arts", "meditation",
            "metal-detecting", "model-trains", "origami", "paragliding",
            "parkour", "pilates", "podcasting", "quilting", "rock-climbing",
            "rowing", "sailing", "scrapbooking", "scuba-diving", "sewing",
            "skiing", "skydiving", "snowboarding", "stand-up-comedy",
            "stained-glass", "street-art", "table-tennis", "taxidermy",
            "theatre", "trampolining", "video-editing", "volunteering",
            "weightlifting", "wine-tasting", "writing", "zumba", "basketball",
            "cricket", "rugby", "badminton", "golf", "fencing", "triathlon"
        ],
        "music": [
            "rock", "pop", "jazz", "classical", "hiphop", "metal", "indie",
            "rnb", "country", "electronic", "folk", "blues", "reggae", "punk",
            "soul", "alternative", "techno", "disco", "ambient", "baroque",
            "bossa-nova", "celtic", "choral", "dancehall", "drum-and-bass",
            "dubstep", "flamenco", "funk", "garage", "gospel", "grunge",
            "grime", "house", "k-pop", "latin", "lo-fi", "motown", "opera",
            "orchestral", "post-rock", "psych-rock", "rap", "salsa", "ska",
            "swing", "trance", "trip-hop", "world-music", "afrobeats",
            "bluegrass", "bolero", "cumbia", "fado", "hardstyle", "merengue",
            "neo-soul", "new-wave", "noise", "prog-rock", "shoegaze", "synth-pop"
        ],
        "education": [
            "engineering", "medicine", "law", "art", "science", "business",
            "history", "psychology", "mathematics", "philosophy", "literature",
            "economics", "architecture", "computing", "biology", "chemistry",
            "physics", "geography", "sociology", "anthropology", "archaeology",
            "astronomy", "biochemistry", "criminology", "dentistry", "design",
            "drama", "education", "environmental-science", "finance", "genetics",
            "geology", "graphic-design", "international-relations", "journalism",
            "linguistics", "marketing", "mechanical-engineering", "microbiology",
            "music", "neuroscience", "nursing", "nutrition", "optometry",
            "pharmacy", "photography", "political-science", "public-health",
            "robotics", "social-work", "software-engineering", "statistics",
            "theology", "urban-planning", "veterinary", "zoology"
        ],
        "politics": [
            "left", "centre", "right", "green", "liberal", "conservative",
            "socialist", "libertarian", "progressive", "moderate", "anarchist",
            "centrist", "communist", "democrat", "environmentalist", "feminist",
            "nationalist", "pacifist", "republican", "social-democrat",
            "traditionalist", "utilitarian", "reformist", "populist"
        ],
        "languages": [
            "english", "spanish", "french", "german", "mandarin", "arabic",
            "portuguese", "italian", "japanese", "hindi", "russian", "korean",
            "afrikaans", "albanian", "amharic", "armenian", "azerbaijani",
            "basque", "bengali", "bosnian", "bulgarian", "catalan", "croatian",
            "czech", "danish", "dutch", "estonian", "farsi", "finnish",
            "georgian", "greek", "gujarati", "hausa", "hebrew", "hungarian",
            "icelandic", "indonesian", "irish", "kannada", "kazakh", "latvian",
            "lithuanian", "macedonian", "malay", "maltese", "marathi", "mongolian",
            "nepali", "norwegian", "pashto", "polish", "punjabi", "romanian",
            "serbian", "sinhalese", "slovak", "slovenian", "somali", "swahili",
            "swedish", "tagalog", "tamil", "telugu", "thai", "turkish",
            "ukrainian", "urdu", "uzbek", "vietnamese", "welsh", "yoruba", "zulu"
        ],
        "religion": [
            "christian", "muslim", "jewish", "hindu", "buddhist", "atheist",
            "agnostic", "spiritual", "sikh", "secular", "bahai", "cao-dai",
            "confucian", "druid", "gnostic", "jain", "pagan", "rastafari",
            "shinto", "taoist", "unitarian", "wiccan", "zoroastrian",
            "non-religious", "humanist", "animist", "indigenous-spirituality"
        ]
    }

    users_to_insert = []
    messages_to_insert = []

    for i in range(1000):
        all_pairs = [(cat, val) for cat, vals in keyword_pools.items() for val in vals]
        picked = random.sample(all_pairs, 50)
        keyword_str = ",".join(f"{cat}:{val}" for cat, val in picked)

        first = random.choice(first_names)
        last = random.choice(last_names)
        email = f"{first.lower()}.{last.lower()}{i}{random.randint(100,999)}@test.com"

        users_to_insert.append({
            "email": email,
            "password": generate_password_hash("Test123!"),
            "name": f"{first} {last}",
            "phone": "07" + "".join([str(random.randint(0, 9)) for _ in range(9)]),
            "age": random.randint(18, 45),
            "gender": random.choice(genders),
            "location": random.choice(locations),
            "non_negotiables": ""
        })

        messages_to_insert.append({
            "user_email": email,
            "keywords": keyword_str
        })

    db.users.insert_many(users_to_insert)
    db.messages.insert_many(messages_to_insert)

    return "Created 1000 users successfully."

def run_search_for_all_users(app):
    with app.app_context():
        db = app.db
        print("Loading all users into memory...")

        all_users = {str(u["_id"]): u for u in db.users.find()}
        all_messages = list(db.messages.find())

        # build keyword lookup
        keyword_map = {}
        for msg in all_messages:
            email = msg.get("user_email")
            kw = msg.get("keywords", "0")
            if email and kw and kw != "0":
                keyword_map.setdefault(email, []).append(kw)

        keyword_strings = {email: ",".join(kws) for email, kws in keyword_map.items()}

        user_list = list(all_users.values())
        total = len(user_list)
        print(f"Processing {total} users...")

        updates = []

        for i, user in enumerate(user_list):
            try:
                my_id = user["_id"]
                my_id_str = str(my_id)
                my_email = user.get("email", "")
                my_keywords = keyword_strings.get(my_email, "")

                buddy_dict = {}

                for j in range(3):
                    # pick random starting user that isn't me
                    candidates_pool = [u for u in user_list if str(u["_id"]) != my_id_str]
                    if not candidates_pool:
                        break

                    best_user = random.choice(candidates_pool)
                    best_id_str = str(best_user["_id"])

                    # score the starting user
                    start_keywords = keyword_strings.get(best_user.get("email", ""), "")
                    _, __, best_score = calculate_match_score(
                        my_keywords, start_keywords, my_id, best_user["_id"]
                    )

                    for k in range(4):
                        current_user = all_users.get(best_id_str)
                        if not current_user:
                            break

                        # check current user and all their buddies
                        candidates = [best_id_str] + list(current_user.get("buddies", {}).values())

                        for candidate_id_str in candidates:
                            if candidate_id_str == my_id_str:
                                continue
                            candidate = all_users.get(candidate_id_str)
                            if not candidate:
                                continue

                            candidate_keywords = keyword_strings.get(candidate.get("email", ""), "")

                            # use calculate_match_score for every comparison
                            _, __, score = calculate_match_score(
                                my_keywords, candidate_keywords,
                                my_id, candidate["_id"]
                            )

                            if score > best_score:
                                best_score = score
                                best_id_str = candidate_id_str

                    buddy_dict[str(j)] = best_id_str

                updates.append({
                    "filter": {"_id": my_id},
                    "update": {"$set": {"buddies": buddy_dict}}
                })

                if (i + 1) % 50 == 0:
                    print(f"[{i+1}/{total}] Processed...")

            except Exception as e:
                print(f"Failed for {user.get('email')}: {e}")

        # write all updates in one bulk operation
        print("Writing to database...")
        from pymongo import UpdateOne
        if updates:
            db.users.bulk_write([
                UpdateOne(u["filter"], u["update"]) for u in updates
            ])

        print(f"All done. {len(updates)} users updated.")

def run_search_for_current_user():
    """Runs search for the current session user. Call this anywhere."""
    db = current_app.db
    user_email = session.get("user_email")

    me = db.users.find_one({"email": user_email})
    if not me:
        return

    my_id = me["_id"]
    my_id_str = str(my_id)

    other_users = {str(u["_id"]): u for u in db.users.find({"email": {"$ne": user_email}})}

    all_messages = list(db.messages.find())
    keyword_map = {}
    for msg in all_messages:
        email = msg.get("user_email")
        kw = msg.get("keywords", "0")
        if email and kw and kw != "0":
            keyword_map.setdefault(email, []).append(kw)

    keyword_strings = {email: ",".join(kws) for email, kws in keyword_map.items()}
    my_keywords = keyword_strings.get(user_email, "")
    user_list = list(other_users.values())

    buddy_dict = {}

    for j in range(3):
        best_user = random.choice(user_list)
        best_id_str = str(best_user["_id"])

        start_keywords = keyword_strings.get(best_user.get("email", ""), "")
        _, __, best_score = calculate_match_score(
            my_keywords, start_keywords, my_id, best_user["_id"]
        )

        for k in range(4):
            current_user = other_users.get(best_id_str)
            if not current_user:
                break

            candidates = [best_id_str] + list(current_user.get("buddies", {}).values())

            for candidate_id_str in candidates:
                if candidate_id_str == my_id_str:
                    continue
                candidate = other_users.get(candidate_id_str)
                if not candidate:
                    continue

                candidate_keywords = keyword_strings.get(candidate.get("email", ""), "")
                _, __, score = calculate_match_score(
                    my_keywords, candidate_keywords,
                    my_id, candidate["_id"]
                )

                if score > best_score:
                    best_score = score
                    best_id_str = candidate_id_str

        buddy_dict[str(j)] = best_id_str
        print(f"Buddy {j}: {other_users[best_id_str].get('email')} (score: {best_score})")

    db.users.update_one(
        {"_id": my_id},
        {"$set": {"buddies": buddy_dict}}
    )
    print(f"Search complete for {user_email}")

@main.route("/run_search")
def run_search():
    if "user_email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))
    try:
        run_search_for_current_user()
        flash("Buddies updated!", "success")
    except Exception as e:
        print(f"Search failed: {e}")
        flash("Search failed — please try again.", "error")
    return redirect(url_for("main.dashboard"))


@main.route("/find_group")
def find_group():
    if "user_email" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("main.login"))

    # run search first to get fresh buddies before forming group
    try:
        run_search_for_current_user()
    except Exception as e:
        print(f"Search failed before group formation: {e}")

    group_id = form_and_save_group()
    if not group_id:
        flash("Couldn't form a group — chat with Jenna first!", "error")
        return redirect(url_for("main.dashboard"))

    members = get_group_members(group_id)
    my_id = get_id_from_email(session.get("user_email"))
    my_keywords = ",".join(get_user_keywords(my_id))

    member_data = []
    for member in members:
        if member["_id"] == my_id:
            continue
        other_keywords = ",".join(get_user_keywords(member["_id"]))
        _, __, score = calculate_match_score(my_keywords, other_keywords, my_id, member["_id"])
        member_data.append({
            "id": str(member["_id"]),
            "name": member.get("name", "Unknown"),
            "age": member.get("age", "?"),
            "gender": member.get("gender", "?"),
            "location": member.get("location", "?"),
            "score": score,
            "keyword_list": parse_keyword_list(other_keywords)
        })

    return render_template("group.html", members=member_data)

# background worker — no route decorator
def run_search_for_all_users_worker(app):
    with app.app_context():
        db = app.db
        print("Loading all users into memory...")

        all_users = {str(u["_id"]): u for u in db.users.find()}
        all_messages = list(db.messages.find())

        keyword_map = {}
        for msg in all_messages:
            email = msg.get("user_email")
            kw = msg.get("keywords", "0")
            if email and kw and kw != "0":
                keyword_map.setdefault(email, []).append(kw)

        keyword_strings = {email: ",".join(kws) for email, kws in keyword_map.items()}

        user_list = list(all_users.values())
        total = len(user_list)
        print(f"Processing {total} users...")

        updates = []

        for i, user in enumerate(user_list):
            try:
                my_id = user["_id"]
                my_id_str = str(my_id)
                my_email = user.get("email", "")
                my_keywords = keyword_strings.get(my_email, "")

                buddy_dict = {}

                for j in range(3):
                    candidates_pool = [u for u in user_list if str(u["_id"]) != my_id_str]
                    if not candidates_pool:
                        break

                    best_user = random.choice(candidates_pool)
                    best_id_str = str(best_user["_id"])

                    start_keywords = keyword_strings.get(best_user.get("email", ""), "")
                    _, __, best_score = calculate_match_score(
                        my_keywords, start_keywords, my_id, best_user["_id"]
                    )

                    for k in range(4):
                        current_user = all_users.get(best_id_str)
                        if not current_user:
                            break

                        candidates = [best_id_str] + list(current_user.get("buddies", {}).values())

                        for candidate_id_str in candidates:
                            if candidate_id_str == my_id_str:
                                continue
                            candidate = all_users.get(candidate_id_str)
                            if not candidate:
                                continue

                            candidate_keywords = keyword_strings.get(candidate.get("email", ""), "")
                            _, __, score = calculate_match_score(
                                my_keywords, candidate_keywords,
                                my_id, candidate["_id"]
                            )

                            if score > best_score:
                                best_score = score
                                best_id_str = candidate_id_str

                    buddy_dict[str(j)] = best_id_str

                updates.append({
                    "filter": {"_id": my_id},
                    "update": {"$set": {"buddies": buddy_dict}}
                })

                if (i + 1) % 50 == 0:
                    print(f"[{i+1}/{total}] Processed...")

            except Exception as e:
                print(f"Failed for {user.get('email')}: {e}")

        print("Writing to database...")
        from pymongo import UpdateOne
        if updates:
            db.users.bulk_write([
                UpdateOne(u["filter"], u["update"]) for u in updates
            ])
        print(f"All done. {len(updates)} users updated.")


# route that triggers the worker
@main.route("/run-search-all")
def run_search_all():
    app = current_app._get_current_object()
    thread = Thread(target=run_search_for_all_users_worker, args=(app,))
    thread.start()
    return "Search started in background — check your terminal for progress."