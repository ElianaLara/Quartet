from flask import render_template, redirect, url_for, session, Blueprint, flash, request, current_app
from .forms import LoginForm, RegisterForm
from flask import current_app

main = Blueprint("main", __name__)


@main.route('/')
def dashboard():
    return render_template('start.html', form=LoginForm())


@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    db = current_app.db

    if form.validate_on_submit():
        db = current_app.db

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

        db.users.insert_one(user_data)

        flash("Registration successful!", "success")
        return redirect(url_for("main.register"))

    return render_template("register.html", form=form)