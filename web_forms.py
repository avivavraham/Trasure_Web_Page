from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, PasswordField, BooleanField, FloatField
from wtforms.validators import DataRequired, EqualTo, NumberRange


# The Different Types Of Forms Are:
# User, Namer, Password, Post, Login
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    age = IntegerField("Age")
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2',
                                                                                  message='Passwords Must Match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")


class PasswordForm(FlaskForm):
    email = StringField("What's your email", validators=[DataRequired()])
    password_hash = PasswordField("What's your password", validators=[DataRequired()])
    submit = SubmitField("Submit")

'''
class BinForm(FlaskForm):
    height = FloatField("Height of bin",
                        validators=[DataRequired(), NumberRange(min=0,
                                                                message="height must have a non-negative value")])
    width = FloatField("Width of bin",
                        validators=[DataRequired(), NumberRange(min=0,
                                                                message="width must have a non-negative value")])
    depth = FloatField("Depth of bin",
                       validators=[DataRequired(), NumberRange(min=0,
                                                               message="depth must have a non-negative value")])
    level = FloatField("Level of bin",
                       validators=[DataRequired(), NumberRange(min=0,
                                                               message="level must have a non-negative value")])
    latitude = FloatField("Latitude of bin", validators=[DataRequired()])
    longitude = FloatField("Longitude of bin", validators=[DataRequired()])
    available = BooleanField("should be picked up or not")
    released = BooleanField("no worker is currently on about to pick it up")
    submit = SubmitField("Submit")
'''


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")
