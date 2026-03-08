from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, IntegerField, EmailField, PasswordField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError, NumberRange
import re


def validate_password(form, field):
    if not re.fullmatch(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$", field.data):
        raise ValidationError('Password must contain at least one uppercase letter, lowercase letter, digit and special character.')
    if re.fullmatch(r"^(?=.*\s).+$", field.data):
        raise ValidationError('Password cannot contain whitespaces.')

def validate_phonenumber(form, field):
    if not re.fullmatch(r"\d+", field.data):
        raise ValidationError('Must be numbers.')

def sanitise_blacklist(form, field):
    if field.data:
        field.data = re.sub(r"[<>]", "", field.data)

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired("Email is required")])
    password = PasswordField('Password', validators=[DataRequired("Password is required")])

    submit = SubmitField("Go to Dashboard")


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired("Email is required"), Email("Incorrect Format")])
    password = PasswordField('Password', validators=[DataRequired("Password if required"), Length(min=6, message="Password must be over 6 in length"), validate_password])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=11, max=11, message="Phone number must be 11 digits (07)"), validate_phonenumber])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=18, message="Under 18s not allowed")])
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")])
    location = StringField('location', validators=[DataRequired()])

    register = SubmitField("Register")

class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    phone = StringField("Phone", validators=[Optional(), Length(min=11, max=11, message="Phone number must be 11 digits (07)"), validate_phonenumber])
    age = IntegerField("Age", validators=[Optional(), NumberRange(min=18, message="Under 18s not allowed")])
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")])
    non_negotiables = TextAreaField("Non-Negotiables / Black List", validators=[Optional(), Length(max=500), sanitise_blacklist])
    submit = SubmitField("Update Profile")