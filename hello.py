from flask import Flask, render_template, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
# create a flask instance
app = Flask(__name__)


# create a route decorator
@app.route('/')
def index():
    return render_template("index.html")


# localhost:5000/user/Aviv
@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)


# create a custom error page

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


# Internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html")

# Create a name Page
@app.route('/name', methods=['GET','POST'])
def name():
    name = None
    form = NamerForm()
    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully")

    return render_template("name.html",
                           name=name,
                           form=form)

# TODO: modified your secret key for form security
app.config['SECRET_KEY'] = "my super secret key that no one shuld know"

# create a form class
class NamerForm(FlaskForm):
    name = StringField("What's your name", validators=[DataRequired()])
    submit = SubmitField("Submit")
