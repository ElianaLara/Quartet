from flask import render_template, redirect, url_for, session, Blueprint, flash, request, current_app
from .forms import LoginForm, RegisterForm

main = Blueprint("main", __name__)




@main.route('/', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db = current_app.db

        # Find the user by email
        user = db.users.find_one({"email": form.email.data})

        if user:
            # NOTE: For production, hash passwords! Here we just compare plaintext
            if user['password'] == form.password.data:
                # Login successful, store user in session
                session['user_email'] = user['email']
                flash("Login successful!", "success")
                return redirect(url_for("main.dashboard"))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("User not found.", "error")

    return render_template("start.html", form=form)

    return render_template('start.html', form=LoginForm())

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