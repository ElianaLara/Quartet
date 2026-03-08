from flask import render_template, redirect, url_for, session, Blueprint, flash, request, current_app
from .forms import LoginForm, RegisterForm, ProfileForm
from Chatbot import intro, send_answer, extract_keywords

main = Blueprint("main", __name__)

chat_messages = []



@main.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db = current_app.db

        # Find the user by email
        user = db.users.find_one({"email": form.email.data})

        if user:
            # NOTE: For production, hash passwords instead of plaintext
            if user['password'] == form.password.data:
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
        non_negotiables=user.get("non_negotiables", "")
    )

    if form.validate_on_submit():
        updated_data = {
            "name": form.name.data,
            "email": form.email.data,
            "phone": form.phone.data,
            "age": form.age.data,
            "gender": form.gender.data,
            "non_negotiables": form.non_negotiables.data
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
            "password": form.password.data,
            "phone": form.phone.data,
            "age": form.age.data,
            "gender": form.gender.data
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
    data = request.json
    text = data.get("message", "").strip()
    if not text:
        return {"status": "error", "message": "Empty message"}, 400

    # Store message from browser user
    chat_messages.append({
        "sender": session.get("user_email", "You"),
        "text": text
    })

    chat_messages.append({
        "sender": session.get("Jenna"),
        "text": send_answer(text)
    })

    chat_messages.append({
        "sender": session.get("Extracted"),
        "text": extract_keywords(text)
    })

    return {"status": "success"}


@main.route("/get_messages")
def get_messages():
    return {"messages": chat_messages}


def add_terminal_message(msg):
    """Simulate another user sending a message from the terminal"""
    chat_messages.append({
        "sender": "Genna",  # or any name you want
        "text": msg
    })

@main.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user_email", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
