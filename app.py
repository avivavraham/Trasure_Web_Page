from flask import Flask, render_template, flash, request, redirect, url_for
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from web_forms import LoginForm, UserForm, PasswordForm
import requests
from datetime import datetime, timedelta

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
@app.route('/', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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


# Auxiliary functions for time formatting
def parse_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")


def check_time_difference(last_time_str):
    last_time = parse_timestamp(last_time_str)
    current_time = datetime.utcnow()
    time_difference = current_time - last_time
    return time_difference > timedelta(hours=8)


def format_timestamp(timestamp_str):
    return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")


def friendly_timedelta(delta):
    if isinstance(delta, timedelta):
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 1:
            return f"{days} days"
        if days == 1:
            return f"{days} day"
        elif hours > 0:
            return f"{hours} hours"
        elif minutes > 0:
            return f"{minutes} minutes"
        else:
            return f"{seconds} seconds"
    else:
        return ""


app.jinja_env.filters['friendly_timedelta'] = friendly_timedelta


# All the problematic Bins(bins that haven't been released/available for a long time)
@app.route('/bins')
@login_required
def bins():
    # Grab all the bins from the cloud
    bins = get_bins()
    problematic_bins = []
    for bin in bins:
        if (not bin.status and check_time_difference(bin.last_acquire_time)) or (bin.availability and check_time_difference(bin.last_pickup_time)):
            problematic_bins.append(bin)
    return render_template("bins.html", bins=problematic_bins,
                           format_timestamp=format_timestamp, current_time=datetime.utcnow())


# shows bin Attributes
@app.route('/bin/<string:id>')
def bin(id):
    bins = get_bins()
    for user_bin in bins:
        if user_bin.id == id:
            return render_template('bin.html', bin=user_bin,
                                   format_timestamp=format_timestamp, current_time=datetime.utcnow())
    flash("Bin is not found")
    return render_template("bins.html", bins=bins,
                           format_timestamp=format_timestamp, current_time=datetime.utcnow())


# make bin available using Azure function app
@app.route('/make_available/<string:id>', methods=['GET', 'POST'])
@login_required
def make_available(id):
    bins = get_bins()
    for user_bin in bins:
        if user_bin.id == id:
            bin = user_bin
            # Update Database

            # perform get request to relevant azure function
            response = requests.get(f"https://smartbinnetworkmainfunctionapp.azurewebsites.net/api/makebinavailable?code=mS9iSxb1sUIMtICiyMHOqvPyN6WqS9GLtSnrUnjIsMczAzFuPaI-Sg%3D%3D&bin_id={user_bin.id}")

            # if response is successful, show success flash message
            if response.status_code >= 200 and response.status_code < 300:
                bin.availability = True
                flash(f"made bin {user_bin.id} available!")

            # else show error flash message
            else:
                flash("error - couldn't make available the bin")

            # redirect to bin (to reload certain information if needed)            
            return redirect(url_for('bin', id=bin.id))
    else:
        flash("You Aren't Authorized to edit this bin")
        bins = get_bins()
        return render_template("bins.html", bins=bins)


# remove bin ownership using Azure function app
@app.route('/remove_ownership/<string:id>', methods=['GET', 'POST'])
@login_required
def remove_ownership(id):
    bins = get_bins()
    for user_bin in bins:
        if user_bin.id == id:
            bin = user_bin
            
            # perform get request to relevant azure function
            response = requests.get(f"https://smartbinnetworkmainfunctionapp.azurewebsites.net/api/freebinownership?code=ElseYU9NKPIGWWgfBRxOueiYfXvAeu6NMYVL4HlPJKsdAzFup39Pxg%3D%3D&bin_id={user_bin.id}")

            # if response is successful, show success flash message
            if response.status_code >= 200 and response.status_code < 300:
                flash(f"removed ownership from bin {user_bin.id}")

            # else show error flash message
            else:
                flash(f"error removing ownership from bin {user_bin.id}")

            # redirect to bin page
            return redirect(url_for('login'))
    else:
        flash("You Aren't Authorized to edit this bin")
        bins = get_bins()
        return render_template("bins.html", bins=bins)


# presenting a scatter map with all the bins in it.
@app.route('/scatter_map')
@login_required
def scatter_map():
    # Get the logged-in user's ID
    user_id = current_user.id
    user_bins = get_bins()
    # Extract latitude and longitude data for each bin
    levels = [bin.level/bin.depth * 100 for bin in user_bins]
    latitudes = [bin.latitude for bin in user_bins]
    longitudes = [bin.longitude for bin in user_bins]
    ids = [bin.id for bin in user_bins]
    return render_template('scatter_map.html', latitudes=latitudes, longitudes=longitudes, levels=levels, ids=ids)


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
@app.route('/update/<string:id>', methods=['GET', 'POST'])
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
class Bins:
    def __init__(self, partition_key, row_key, latitude, longitude, width,
                 height, depth, level, status, availability, last_acquire_time, last_pickup_time):
        self.partition_key = partition_key
        self.id = row_key
        self.latitude = latitude
        self.longitude = longitude
        self.width = width
        self.height = height
        self.depth = depth
        self.level = level
        self.status = (status == "Released")
        self.availability = (availability == "Available")
        self.last_acquire_time = last_acquire_time
        self.last_pickup_time = last_pickup_time


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
    # bins = db.relationship('Bins', backref='poster')

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


# Getting all the bins from the appropriate Azure Function app.
def get_bins():
    try:
        # URL to fetch bins data
        url = "https://smartbinnetworkmainfunctionapp.azurewebsites.net/api/getallbins?code=dbP4EdbYUOxkI7ujXDGPimwAGy4EplPSlU7UVPsL2oicAzFuhtKZAg%3D%3D"

        # Make GET request to the URL
        response = requests.get(url)
        json_response = response.json()
        # Convert JSON response to a list of Bins objects
        user_bins = []
        for bin_data in json_response:
            if bin_data["PartitionKey"] == "Bin":
                bin_obj = Bins(
                    partition_key="Bin",
                    row_key=bin_data["RowKey"],
                    latitude=bin_data["bin_latitude"],
                    longitude=bin_data["bin_longitude"],
                    width=bin_data["bin_width_cm"],
                    height=bin_data["bin_height_cm"],
                    depth=bin_data["bin_depth_cm"],
                    level=bin_data["bin_level_cm"],
                    status=bin_data["bin_status"],
                    availability=bin_data["bin_availability"],
                    last_acquire_time=bin_data["last_acquire_time"],
                    last_pickup_time=bin_data["last_pickup_time"]
                )
                user_bins.append(bin_obj)
        return user_bins
    except:
        # Return an error message
        flash("Whoops! There was a problem getting the bins, please try again...")
        return []

'''

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

'''
'''
@app.route('/make_released/<string:id>', methods=['GET', 'POST'])
@login_required
def make_released(id):
    bins = get_bins()
    for user_bin in bins:
        if user_bin.id == id:
            bin = user_bin
            # Update Database
            # TODO: How to update bin data
            bin.status = True
            flash("Bin Has Made Released!")
            return redirect(url_for('bin', id=bin.id))
    else:
        flash("You Aren't Authorized to edit this bin")
        bins = get_bins()
        return render_template("bins.html", bins=bins)
'''
