import os
import shutil
from model import *
from glob import glob
from utils import applyFormData, user_assigned_assessment
from flask_security import auth_required, roles_accepted, current_user
from flask import Blueprint, render_template, request, jsonify
from blueprints.assessment_utils import assessmenthexagons

blueprint_assessment = Blueprint('blueprint_assessment', __name__)

@blueprint_assessment.route('/assessment', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
def newassessment():
    assessment = Assessment(
        name = request.form['name'],
        description = request.form['description']
    )
    assessment.save()

    if not os.path.exists(f"files/{str(assessment.id)}"):
        os.makedirs(f"files/{str(assessment.id)}")

    return jsonify(assessment.to_json()), 200

@blueprint_assessment.route('/assessment/<id>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
def editassessment(id):
    assessment = Assessment.objects(id=id).first()
    assessment = applyFormData(assessment, request.form, ["name", "description"])
    assessment.save()
    
    return jsonify(assessment.to_json()), 200

@blueprint_assessment.route('/assessment/<id>', methods = ['DELETE'])
@auth_required()
@roles_accepted('Admin')
def deleteassessment(id):
    assessment = Assessment.objects(id=id).first()
    [testcase.delete() for testcase in TestCase.objects(assessmentid=id).all()]
    if os.path.exists(f"files/{str(assessment.id)}"):
        shutil.rmtree(f"files/{str(assessment.id)}")
    assessment.delete()
    return "", 200

@blueprint_assessment.route('/assessment/<id>', methods = ['GET'])
@auth_required()
@user_assigned_assessment
def loadassessment(id):
    return render_template(
        'assessment.html',
        testcases = TestCase.objects(assessmentid=id, deleted=False).all(),
        deleted_testcases = TestCase.objects(assessmentid=id, deleted=True).all(),
        assessment = Assessment.objects(id=id).first(),
        templates = TestCaseTemplate.objects(),
        mitres = sorted(
            [[m["mitreid"], m["name"]] for m in Technique.objects()],
            key=lambda m: m[0]
        ),
        tactics = [tactic["name"] for tactic in Tactic.objects()],
        hexagons = assessmenthexagons(id),
        reports = [f.split("/")[-1] for f in sorted(glob("custom/reports/*.docx"))]
    )