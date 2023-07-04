from model import *
from flask_security import auth_required, roles_accepted
from flask import Blueprint, render_template, request, session
# from blueprints.assessment_utils import generatestats

blueprint_assessment = Blueprint('blueprint_assessment', __name__)

@blueprint_assessment.route('/assessment/new', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
def newassessment():
    if request.method == 'POST':
        # TODO way to import custom packs of tools/controls
        assessment = Assessment(
            name = request.form['name'],
            description = request.form['description'],
            tools = [Tool(name="Sample Tool", description="Sample Desc")],
            controls = [Control(name="Sample Control", description="Sample Desc")]
        )
        assessment.save()

        return {"id": str(assessment.id)}, 200

@blueprint_assessment.route('/assessment/<id>', methods = ['GET'])
@auth_required()
def loadassessment(id):
    session["assessmentid"] = id

    # stats = generatestats(tests, ass)

    return render_template(
        'assessment.html',
        tests = TestCase.objects(assessmentid=id).all(),
        ass = Assessment.objects(id=id).first(),
        templates = TestCaseTemplate.objects(),
        mitres = [
            [m["mitreid"], m["name"]] for m in Technique.objects()
        ].sort(key=lambda x: x[0]),
        # stats=stats
    )