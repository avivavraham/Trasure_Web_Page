from flask import Flask, render_template, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate

# create a flask instance
app = Flask(__name__)
# Old SQLAlchemy Data Base
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# New MYSQL Data Base
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/our_users'
# TODO: modified your secret key for form security
app.config['SECRET_KEY'] = "my super secret key that no one should know"
# Initialize the Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.app_context().push()


# create Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    age = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name


# create a form class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    age = IntegerField("Age")
    submit = SubmitField("Submit")


class NamerForm(FlaskForm):
    name = StringField("What's your name", validators=[DataRequired()])
    submit = SubmitField("Submit")


with app.app_context():
    db.create_all()


# localhost:5000/user/Aviv
@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)


# create a route decorator
@app.route('/')
def index():
    return render_template("index.html")


# Update Data Base Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.age = request.form['age']
        try:
            db.session.commit()
            flash("User Updated Successfully")
            return render_template("update.html",
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
        except:
            db.session.commit()
            flash("Error! Looks like there was a problem...\tplease try again. ")
            return render_template("update.html",
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
    else:
        return render_template("update.html",
                               form=form,
                               name_to_update=name_to_update,
                               id=id)


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
@app.route('/name', methods=['GET', 'POST'])
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


# Create a name Page
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            user = Users(name=form.name.data, email=form.email.data, age=form.age.data)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.age.data = 0
        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html",
                           form=form,
                           name=name,
                           our_users=our_users)


# Delete Data Base Record
@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully")
        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html",
                               form=form,
                               name=name,
                               our_users=our_users)
    except:
        flash("Whoops! There was a problem deleting this record...")
        return render_template("add_user.html",
                               form=form,
                               name=name,
                               our_users=our_users)
