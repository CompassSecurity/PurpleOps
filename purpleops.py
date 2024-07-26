import os
from model import *
from dotenv import load_dotenv
from flask import Flask, render_template, redirect
from flask_security import Security, auth_required, current_user

from blueprints import access, assessment, assessment_utils, assessment_import, assessment_export, testcase, testcase_utils


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

db.init_app(app)

security = Security(app, user_datastore)

@app.route('/')
@app.route('/index')
@auth_required()
def index():
    if current_user.initpwd:
        return redirect("/password/change")
    assessments = Assessment.objects().all()
    return render_template('assessments.html', assessments=assessments)

# mitigates cve-2023-49438 - can be removed with Flask-Security-Too >=5.3.3
# see: https://github.com/brandon-t-elliott/CVE-2023-49438
@app.after_request
def fix_location_header(response):
    response.autocorrect_location_header = True
    return response

if __name__ == "__main__":
    app.run(host=os.getenv('HOST'), port=int(os.getenv('PORT')))