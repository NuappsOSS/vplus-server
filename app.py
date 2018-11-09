#!/usr/bin/python
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_wtf import FlaskForm
from flask_googlemaps import GoogleMaps
from flask_qrcode import QRcode
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired #... and other necessary validators
from flask_material import Material

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
Material(app)

def searchQuery(query, reference):
    search = []
    queries = db.reference(reference).get(etag=False)

    for result in queries:
        if result[1] == query:
            search.append(result)

    return search

def employeeTranverse(companyName):
    employees = []
    search = db.reference("employees/").get(etag=False)

    for employee in search:
        if employee[7] == companyName:
            employees.append(employee)

    return employees


def getCompanies():
    companies = []
    search = db.reference("companies/").get(etag=False)

    searchIter = iter(search)
    next(searchIter)

    for company in searchIter:
        companies.append(company)

    return companies

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

# Redirect to 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/index')
def redirect_to_index():
    return redirect(url_for('index'))

@app.route('/privacypolicy')
def privacy_policy():
    return render_template('privacypolicy.html',
                        title="Privacy Policy")

# Main Page
@app.route('/', methods=['GET', 'POST'])
def index():
    featured = "Nuapps"

    featuredCompany = searchQuery(featured, "companies/")

    if request.method == "POST":
        return redirect(url_for("search", query=request.form["searchQuery"]))

    return render_template('index.html',
                        title="Welcome!",
                        featuredCompany=featuredCompany)

# About Page
@app.route('/about')
def about():
    return render_template('about.html', title="About VEPlus")

@app.route('/list')
def listCompanies():
    companies = getCompanies()
    return render_template('list.html',
                            title="Available Companies",
                            companies=companies)



# Search route for companies
@app.route('/search/?q=<query>', methods=['GET', 'POST'])
def search(query):

    searchCompany = searchQuery(query, "companies/")
    searchEmployee = searchQuery(query, "employees/")

    # Render template
    return render_template('search.html',
                    title="Search Results",
                    searchCompany=searchCompany,
                    searchEmployee=searchEmployee)


# Profile route for employees
@app.route('/profile/<employee_name>', methods=['GET'])
def profile(employee_name):
    search = searchQuery(employee_name, "employees/")

    if search is None:
        flask.abort(404)

    return render_template('profile.html',
                title=employee_name,
                employee=search)

# Profile route for company
@app.route('/company/<company_name>', methods=['GET'])
def company(company_name):

    search = searchQuery(company_name, "companies/")
    employees = employeeTranverse(company_name)

    if search is None:
        flask.abort(404)

    url = request.url + company_name

    return render_template('company.html',
                title=company_name,
                employees=employees,
                url=url,
                company=search)


if __name__ == '__main__':
    app.run()
