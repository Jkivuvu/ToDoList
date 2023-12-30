from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, validators
from wtforms.validators import DataRequired


class Task(FlaskForm):
    List_name = StringField('Please name your task list', validators=[DataRequired()])
    Task = StringField('Enter your task here', validators=[DataRequired()])
    Enter = SubmitField('Enter')


class Registerform(FlaskForm):
    Email = EmailField('Email', validators=[DataRequired()])
    Name = StringField('Name', validators=[DataRequired()])
    Username = StringField('Username', validators=[DataRequired()])
    Password = PasswordField('Password', [validators.DataRequired(), validators.Length(min=6, max=35)])
    Confirm_Password = PasswordField('Confirm Password', [validators.DataRequired(), validators.Length(min=6, max=35)])
    Enter = SubmitField('Register')


class LoginForm(FlaskForm):
    Email = EmailField("Email", validators=[DataRequired()])
    Password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Log In")
