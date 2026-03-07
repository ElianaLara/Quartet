from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, IntegerField, EmailField, PasswordField, DateField, TimeField
from wtforms.validators import DataRequired, Optional

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

    register = SubmitField("Register")