import os
from model import *
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, request
from flask_security import Security, auth_required, current_user

from flask_wtf.csrf import CSRFProtect

from blueprints import access, assessment, assessment_utils, assessment_import, assessment_export, testcase, testcase_utils

import mongoengine as me


load_dotenv()

app = Flask(__name__)

app.config.from_pyfile("flask.cfg")

app.register_blueprint(access.blueprint_access)
app.register_blueprint(assessment.blueprint_assessment)
app.register_blueprint(assessment_utils.blueprint_assessment_utils)
app.register_blueprint(assessment_import.blueprint_assessment_import)
app.register_blueprint(assessment_export.blueprint_assessment_export)
app.register_blueprint(testcase.blueprint_testcase)
app.register_blueprint(testcase_utils.blueprint_testcase_utils)

me.connect(**app.config["MONGODB_SETTINGS"])

security = Security(app, user_datastore)
csrf = CSRFProtect(app)

@app.route('/')
@app.route('/index')
@auth_required()
def index():
    if current_user.initpwd:
        return redirect("/password/change")
    assessments = Assessment.objects().all()
    return render_template('assessments.html', assessments=assessments)

# injects the theme "directory" into every request. So we don't have to rewrite this code on each page render
@app.context_processor
def inject_theme():
    theme = request.cookies.get('theme', 'light')
    return dict(theme=theme)

if __name__ == "__main__":
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')))