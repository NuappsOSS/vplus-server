#!/usr/bin/python
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user
from flask_googlemaps import GoogleMaps
from flask_qrcode import QRcode
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired #... and other necessary validators
from flask_bootstrap import Bootstrap

import os
import urllib
import simplejson
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate('private/serviceAccountKey.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL' : "https://veiplus-96fa7.firebaseio.com/"
})


app = Flask(__name__)

app.secret_key = os.urandom(100)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['GOOGLEMAPS_KEY'] = "AIzaSyBddL64NmxF6-8GVRl4gUvJDCXFf0KmB0w"


GoogleMaps(app)
QRcode(app)
Bootstrap(app)
login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = "login"


class CompanyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    employees = StringField('Employees', validators=[DataRequired()])
    industry = StringField('Industry', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    imgUrl = StringField('Image URL')
    twitter = StringField('Twitter (@handle)')
    facebook = StringField('Facebook (link)')
    website = StringField('Website (url)')
    description = TextAreaField('Description')

class EmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    position = StringField('Job Position', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    twitter = StringField('Twitter')
    email = StringField('Email')
    website = StringField('Website')

def searchForCompany(company_query):
    search = []
    companies = db.reference('companies/').get(etag=False)

    for business in companies.items():
        for key,value in business[1].items():
            if value == company_query:
                search.append(business[1])
    return search


# Combine into funtion that returns tuple
def searchForEmployee(employee_query):
    search = []
    employees = db.reference('employees/').get(etag=False)

    for employee in employees.items():
        for key, value in employee[1].items():
            if value == employee_query:
                search.append(employee[1])

    return search

googleGeocodeUrl = 'http://maps.googleapis.com/maps/api/geocode/json?'

def get_coordinates(query):
    query = str(query).encode('utf-8')
    params = {
        'address': query,
        'sensor': "false"
    }
    url = googleGeocodeUrl + urllib.urlencode(params)
    json_response = urllib.urlopen(url)
    response = simplejson.loads(json_response.read())
    if response['results']:
        location = response['results'][0]['geometry']['location']
        latitude, longitude = location['lat'], location['lng']
        print query, latitude, longitude
    else:
        latitude, longitude = None, None
        print query, "<no results>"
    return latitude, longitude


# Database helpers

class DatabaseHelper(object):

    def __init__(self, query):
        self.query = query

        # Instance variables for calling upon reference
        # to database
        self.root = db.reference()
        self.company = self.root.child('companies')
        self.employee = self.root.child('employees')


    def addNewCompany(self):

        self.company.push({
            'companyName' : '{}'.format(self.query['name']),
            'employees' : '{}'.format(self.query['employees']),
            'industry' : '{}'.format(self.query['industry']),
            'location' : '{}'.format(self.query['location']),
            'imgUrl' : '{}'.format(self.query['imgUrl']),
            'website': '{}'.format(self.query['website']),
            'twitter': '{}'.format(self.query['twitter']),
            'facebook': '{}'.format(self.query['facebook']),
            'description' : '{}'.format(self.query['description']),
            'address': '{}'.format(self.query['address'])
        })


    def addNewEmployee(self):
        self.employee.push({
            'employeeName'  : '{}'.format(self.query['name']),
            'company'       : '{}'.format(self.query['company']),
            'position'      : '{}'.format(self.query['position']),
            'description'   : '{}'.format(self.query['description']),
            'twitter'       : '{}'.format(self.query['twitter']),
            'email'         : '{}'.format(self.query['email']),
            'website'       : '{}'.format(self.query['website'])
        })

@login_manager.user_loader
def load_user(input_key):
    keys = db.reference('invite-keys/').get(etag=False)
    for key in keys:
        if key == input_key:
            return key

    return None



# Redirect to 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/invite', methods=['GET', 'POST'])
def invite():
    if request.method == "POST":

        login_user(request.form['key'])
        flash("Logged in successfully")
        return redirect(url_for('index'))

    return render_template('invite.html')

@app.route('/index')
def redirect_to_index():
    return redirect(url_for('index'))

@app.route('/privacypolicy')
def privacy_policy():
    return render_template('privacypolicy.html',
                        title="Privay Policy")

# Main Page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        return redirect(url_for("search", query=request.form["searchQuery"]))

    return render_template('index.html',
                        title="Welcome!")

# Admin Page
@app.route('/admin', methods = ['GET', 'POST'])
def admin():

    # Forms to render on Admin page
    companyForm = CompanyForm(request.form)
    employeeForm = EmployeeForm(request.form)

    # Check if method is POST (form action occurred)
    if request.method == "POST":
        # Create new object to DatabaseHelper
        obj = DatabaseHelper(request.form)
        # Check if company data or employee data
        if request.form["companyName"]:
            obj.addNewCompany()
            flash("success", "Successfully added new company")
        elif request.form["employeeName"]:
            obj.addNewEmployee()
            flash("success", "Successfully added new employee!")
        # Return to admin page
        return redirect(url_for('admin'))

    # Render template with necessary data
    return render_template('admin.html',
        title="Admin Panel",
        companyForm=companyForm,
        employeeForm=employeeForm)


# About Page
@app.route('/about')
def about():
    return render_template('about.html', title="About VEPlus")


# Search route for companies
@app.route('/search/?q=<query>', methods=['GET', 'POST'])
def search(query):

    searchCompany = searchForCompany(query)
    searchEmployee = searchForEmployee(query)

    # Render template
    return render_template('search.html',
                    title="Search Results",
                    searchCompany=searchCompany,
                    searchEmployee=searchEmployee)


# Profile route for employees
@app.route('/profile/<employee_name>', methods=['GET'])
def profile(employee_name):
    search = searchForEmployee(employee_name)

    if search is None:
        flask.abort(404)

    return render_template('profile.html',
                title=employee_name,
                employee=search)

# Profile route for company
@app.route('/company/<company_name>', methods=['GET'])
def company(company_name):
    search = searchForCompany(company_name)

    if search is None:
        flask.abort(404)

    url = "http://vplus-server.herokuapp.com/company/" + company_name

    return render_template('company.html',
                title=company_name,
                url=url,
                company=search)


app.jinja_env.filters['get_coordinates'] = get_coordinates


if __name__ == '__main__':
    app.run()
