from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from web_forms import LoginForm, BinForm, UserForm, PasswordForm

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

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Apps Routes: Alphabetically Ordered-
# index  '/',
# Add Bin '/add_bin',
# Dashboard 'dashboard',
# Delete '/delete/<int:id>'
# Error handlers
# Login '/login'
# Logout '/logout'
# Name '/name'
# Bins: '/bins', '/bins/<int:id>', '/bins/edit/<int:id>', '/bins/delete/<int:id>'
# Test Password '/test_pw'
# Update '/update/<int:id>'
# User: '/user/<name>', '/user-add'


# create a route decorator
@app.route('/')
def index():
    return render_template("index.html")


# Add Post Page
@app.route('/add_bin', methods=['GET', 'POST'])
@login_required
def add_bin():
    form = BinForm()

    if form.validate_on_submit():
        poster = current_user.id
        released = form.released.data if form.released.data is not None else False
        available = form.available.data if form.available.data is not None else False
        bin = Bins(title=form.title.data, poster_id=poster, height=form.height.data,
                   width=form.width.data, level=form.level.data, depth=form.depth.data,
                   latitude=form.latitude.data, longitude=form.longitude.data,
                   released=form.released.data, available=form.available.data)
        # Clear The Form
        form.title.data = ''
        form.height.data = ''
        form.width.data = ''
        form.level.data = ''
        form.depth.data = ''
        form.latitude.data = ''
        form.longitude.data = ''
        form.released.data = ''
        form.available.data = ''

        # Add post data to database
        db.session.add(bin)
        db.session.commit()

        # Return a Message
        flash("Bin Submitted Successfully!")

    # Redirect to the webpage
    return render_template("add_bin.html", form=form)


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.age = request.form['age']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("dashboard.html",
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("dashboard.html",
                                   form=form,
                                   name_to_update=name_to_update,
                                   id=id)
    else:
        return render_template("dashboard.html",
                               form=form,
                               name_to_update=name_to_update,
                               id=id)


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


# create a custom error page

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


# Internal server error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html")


# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the Password for access
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successfully!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("User Does Not Exist... - Please Try Again!")
    return render_template('login.html', form=form)


# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!  Thanks For Stopping By...")
    return redirect(url_for('login'))


@app.route('/bins')
def bins():
    # Grab all the bins from the data base
    bins = Bins.query.order_by(Bins.date_posted)
    return render_template("bins.html", bins=bins)


@app.route('/bin/<int:id>')
def bin(id):
    bin = Bins.query.get_or_404(id)
    return render_template('bin.html', bin=bin)


@app.route('/bins/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_bin(id):
    bin = Bins.query.get_or_404(id)
    form = BinForm()
    if form.validate_on_submit():
        bin.title = form.title.data
        bin.height = form.height.data
        bin.width = form.width.data
        bin.level = form.level.data
        bin.depth = form.depth.data
        bin.latitude = form.latitude.data
        bin.longitude = form.longitude.data
        bin.released = form.released.data if form.released.data is not None else False
        bin.available = form.available.data if form.available.data is not None else False
        # Update Database
        db.session.add(bin)
        db.session.commit()
        flash("Bin Has Been Updated!")
        return redirect(url_for('bin', id=bin.id))
    if current_user.id == bin.poster_id:
        form.title.data = bin.title
        form.height.data = bin.height
        form.width.data = bin.width
        form.level.data = bin.level
        form.depth.data = bin.depth
        form.latitude.data = bin.latitude
        form.longitude.data = bin.longitude
        form.released.data = bin.released
        form.available.data = bin.available
        return render_template('edit_bin.html', form=form)
    else:
        flash("You Aren't Authorized to edit this bin")
        bins = Bins.query.order_by(Bins.date_posted)
        return render_template("bins.html", bins=bins)


@app.route('/bins/delete/<int:id>')
@login_required
def delete_bin(id):
    bin_to_delete = Bins.query.get_or_404(id)
    id = current_user.id
    if id == bin_to_delete.poster.id:
        try:
            db.session.delete(bin_to_delete)
            db.session.commit()
            # Return a message
            flash("Bin Was Deleted!")
            # Grab all the bins from the database
            bins = Bins.query.order_by(Bins.date_posted)
            return render_template("bins.html", bins=bins)

        except:
            # Return an error message
            flash("Whoops! There was a problem deleting bin, try again...")
            # Grab all the bins from the database
            bins = Bins.query.order_by(Bins.date_posted)
            return render_template("bins.html", bins=bins)
    else:
        # Return a message
        flash("You Aren't Authorized To Delete That Bin!")
        # Grab all the bins from the database
        bins = Bins.query.order_by(Bins.date_posted)
        return render_template("bins.html", bins=bins)


# Create Password Test Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        # clearing the Form
        form.email.data = ''
        form.password_hash.data = ''
        # Look up user by email address
        pw_to_check = Users.query.filter_by(email=email).first()
        # Check Hashed Password
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template("test_pw.html",
                           email=email,
                           password=password,
                           pw_to_check=pw_to_check,
                           passed=passed,
                           form=form)


# Update Data Base Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.age = request.form['age']
        name_to_update.username = request.form['username']
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



# Adding a new user
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hashing password!
            hashed_pw = generate_password_hash(form.password_hash.data)
            user = Users(username=form.username.data, name=form.name.data, email=form.email.data, age=form.age.data,
                         password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.age.data = 0
        form.password_hash.data = ''
        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html",
                           form=form,
                           name=name,
                           our_users=our_users)


# Classes-

# Create a Bin model
class Bins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # An optional bin name
    title = db.Column(db.String(255))
    height = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=False)
    level = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    available = db.Column(db.Boolean)
    released = db.Column(db.Boolean)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    # Foreign Key To Link Users(refer to primary key of the user)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    age = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=datetime.utcnow())
    # Security - password
    password_hash = db.Column(db.String(128))
    # User Can Have Many Bins
    bins = db.relationship('Bins', backref='poster')

    @property
    def password(self):
        raise AttributeError('password is not readable attribute!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create a string
    def __repr__(self):
        return '<Name %r>' % self.name


with app.app_context():
    db.create_all()
