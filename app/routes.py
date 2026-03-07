from flask import render_template, redirect, url_for, session, Blueprint, flash, request, current_app

main = Blueprint("main", __name__)


@main.route('/')
def dashboard():
    return render_template('start.html')