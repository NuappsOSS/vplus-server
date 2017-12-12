#!/usr/bin/python
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired #... and other necessary validators
from flask_bootstrap import Bootstrap

import os
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate('private/serviceAccountKey.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL' : "https://veiplus-96fa7.firebaseio.com/"
})


app = Flask(__name__)
app.config.from_object('config')

app.secret_key = os.urandom(100)
app.config['TEMPLATES_AUTO_RELOAD'] = True

Bootstrap(app)
app.secret_key = os.urandom(64)

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


# Database helpers

class DatabaseHelper(object):

    def __init__(self, query):
        self.query = query

        # Instance variables for calling upon reference
        # to database
        self.root = db.reference()
        self.company = self.root.child('companies')
        self.employee = self.root.child('employees')


    # TODO: Address + Social Media + Website
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
            'description' : '{}'.format(self.query['description'])
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


# Redirect to 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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

    return render_template('profile.html',
                title=employee_name,
                employee=search)

# Profile route for company
@app.route('/company/<company_name>', methods=['GET'])
def company(company_name):
    search = searchForCompany(company_name)


    return render_template('company.html',
                title=company_name,
                company=search)

# "unit test"
def test():
    emp = {
        'name'  : "Derek Pastor",
        'company'       : "Nuapps",
        'position'      : "CTO",
        'description'   : "I'm a horrible CTO",
        'twitter'       : "poop",
        'email'         : "derek@derek.com",
        'website'       : "derekpastor.com"
    }

    obj = DatabaseHelper(emp)
    obj.addNewEmployee()

if __name__ == '__main__':
    #test()
    app.run()