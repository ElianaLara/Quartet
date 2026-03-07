from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, IntegerField, EmailField, PasswordField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length, Optional

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    submit = SubmitField("Go to Dashboard")


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    gender = StringField('gender', validators=[DataRequired()])
    location = StringField('location', validators=[DataRequired()])

    register = SubmitField("Register")

class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional(), Length(min=6)])
    phone = StringField("Phone", validators=[Optional(), Length(max=20)])
    age = IntegerField("Age", validators=[Optional()])
    gender = SelectField("Gender", choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")])
    non_negotiables = TextAreaField("Non-Negotiables / Black List", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Update Profile")
