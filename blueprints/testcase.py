import os
from model import *
from utils import *
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, jsonify
from flask_security import auth_required, roles_accepted, current_user

blueprint_testcase = Blueprint('blueprint_testcase', __name__)

@blueprint_testcase.route('/testcase/<id>/single', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
@user_assigned_assessment
def newtestcase(id):
    newcase = TestCase()
    newcase.assessmentid = id
    newcase = applyFormData(newcase, request.form, ["name", "mitreid", "tactic"])
    newcase.save()
    return jsonify(newcase.to_json()), 200

@blueprint_testcase.route('/testcase/<id>',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def runtestcasepost(id):
    testcase = TestCase.objects(id=id).first()
    assessment = Assessment.objects(id=testcase.assessmentid).first()

    if not testcase.visible and current_user.has_role("Blue"):
        return ("", 403)

    return render_template('testcase.html',
        testcase = testcase,
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all(),
        tactics = Tactic.objects().all(),
        assessment = assessment,
        kb = KnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        testcasekb = TestcaseKnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        templates = TestCaseTemplate.objects(mitreid=testcase["mitreid"]),
        mitres = [[m["mitreid"], m["name"]] for m in Technique.objects()],
        sigmas = Sigma.objects(mitreid=testcase["mitreid"]),
        multi = {
            "sources": assessment.sources,
            "targets": assessment.targets,
            "tools": assessment.tools,
            "controls": assessment.controls,
            "tags": assessment.tags,
            "preventionsources": assessment.preventionsources,
            "detectionsources": assessment.detectionsources
        }
    )

def format_time_difference(d1, d2):

    if not d1 or not d2:
        return None

    if d2 > d1:
        return None

    delta = abs(d1-d2)

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")

    return  " ".join(parts)

def calculate_severity_score(severity, expected_severity):
    severity_levels = {
        "Critical": ["Critical"],
        "High": ["Critical", "High"],
        "Medium": ["Critical", "High", "Medium"],
        "Low": ["Critical", "High", "Medium", "Low"],
        "Informational": ["Critical", "High", "Medium", "Low", "Informational"]
    }
    if severity and expected_severity:
        accepted_severity_list = severity_levels.get(expected_severity, [])
        return 100 if severity in accepted_severity_list else 0
    return None
    
@blueprint_testcase.route('/testcase/<id>',methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def testcasesave(id):
    testcase = TestCase.objects(id=id).first()
    isBlue = current_user.has_role("Blue")

    if not testcase.visible and isBlue:
        return ("", 403)

    directFields = ["name", "objective", "actions", "rednotes", "bluenotes", "uuid", "mitreid", "tactic", "state", "preventedrating", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency", "expectedseverity", "incidentseverity"] if not isBlue else ["bluenotes", "prevented", "alerted", "alertseverity","state", "incidentcreated", "incidentseverity"] 
    listFields = ["sources", "targets", "tools", "controls", "tags", "preventionsources", "detectionsources"] if not isBlue else ["tags" , "preventionsources", "detectionsources"]
    boolFields = ["alerted", "logged", "visible", "incidentcreated", "prevented", "expectedincidentcreation", "expectedprevention", "expectedalertcreation"] if not isBlue else ["prevented", "alerted", "logged","incidentcreated"]
    timeFields = ["starttime", "endtime", "alerttime", "preventtime", "incidenttime"] if not isBlue else ["alerttime", "preventtime", "incidenttime"]
    fileFields = ["redfiles", "bluefiles"] if not isBlue else ["bluefiles"]

    # only allow state update from blue if correct state is sent and testcase is in changable state
    if isBlue:
        if request.form.get("state") != 'Waiting Blue' and request.form.get("state") != 'Waiting Red' and request.form.get("state"):
            return ("Not allowed state value", 403)
        if testcase.state != 'Waiting Blue' and testcase.state != 'Waiting Red':
            return ("State cannot be changed at the moment", 403)

    # do not update testcase if it was modified in the meantime
    if request.form.get("modifytime"):
        requestmodifytime = request.form.get("modifytime")
        # ugly string compare of date
        if requestmodifytime != str(testcase.modifytime):
            return ("", 409)

    testcase = applyFormData(testcase, request.form, directFields)
    testcase = applyFormListData(testcase, request.form, listFields)
    testcase = applyFormBoolData(testcase, request.form, boolFields)
    testcase = applyFormTimeData(testcase, request.form, timeFields)

    if not os.path.exists(f"files/{testcase.assessmentid}/{str(testcase.id)}"):
        os.makedirs(f"files/{testcase.assessmentid}/{str(testcase.id)}")

    for field in fileFields:
        files = []
        for file in testcase[field]:
            if file.name.lower().split(".")[-1] in ["png", "jpg", "jpeg"]:
                caption = request.form[field.replace("files", "").upper() + file.name]
            else:
                caption = ""
            files.append({
                "name": secure_filename(file.name),
                "path": file.path,
                "caption": caption
            })
        for file in request.files.getlist(field):
            if request.files.getlist(field)[0].filename:
                filename = secure_filename(file.filename)
                path = f"files/{testcase.assessmentid}/{str(testcase.id)}/{filename}"
                file.save(path)
                files.append({"name": filename, "path": path, "caption": ""})
        if field == "redfiles":
            testcase.update(set__redfiles=files)
        else:
            testcase.update(set__bluefiles=files)

    testcase.modifytime = datetime.utcnow()

    # replace last three digits in the string with "000". Required for comparing utcnow vs. mongodb timestamp
    mongomodifytime = str(testcase.modifytime)[:-3] + "000"

    if "logged" in request.form and request.form["logged"] == "Yes" and not testcase.detecttime:
        testcase.detecttime = datetime.utcnow()

    # Calculate alert severity score
    testcase.alertseverityscore = calculate_severity_score(testcase.alertseverity, testcase.expectedseverity)
    
    # Calculate incident severity score
    testcase.incidentseverityscore = calculate_severity_score(testcase.incidentseverity, testcase.expectedseverity)

    # Calculate testcase outcome (Note that Prevented or alerted but not Logged is not catched and will be "missed")
    if not testcase.logged:
        testcase.outcome = "Missed"
    else:
        if testcase.prevented and testcase.alerted:
            testcase.outcome = "Prevented and Alerted"
        elif testcase.prevented:
            testcase.outcome = "Prevented"
        elif testcase.alerted:
            testcase.outcome = "Alerted"
        else:
            testcase.outcome = "Logged"

    # Calculate testcase score
    criteriacounter = 1
    if testcase.expectedalertcreation:
        criteriacounter = criteriacounter + 1
    if testcase.expectedprevention:
        criteriacounter = criteriacounter + 1
    score = 0

    criteriavalue = 100 / criteriacounter

    if testcase.logged:
        score = score + criteriavalue
    if testcase.expectedalertcreation and  testcase.alerted:
        score = score + criteriavalue
    if testcase.expectedprevention and testcase.prevented:
        score = score + criteriavalue

    testcase.testcasescore = score

    # Calculate event start time to alert time
    diff_result = format_time_difference(testcase.alerttime, testcase.starttime)
    if diff_result is not None:
        testcase.eventtoalert = diff_result
    else:
        testcase.eventtoalert = ""

    # Calculate alert to incident
    diff_result = format_time_difference(testcase.incidenttime, testcase.alerttime)
    if diff_result is not None:
        testcase.alerttoincident = diff_result
    else:
        testcase.alerttoincident = ""

    # This is some sanity check code where we check if some of the UI elements are out of sync with the backend. This is trggered by the horrible tabs bug
    # Does not fix user not saving test case before navigating away
    # Todo: Turns this BS code into a single mongoengine query against the subdocument list
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    for field in listFields:
        ids = []
        valid_ids = []
        for t in assessment[field]:
            ids.append(str(t.id))
        for field_id in testcase[field]:
            if field_id in ids:
                valid_ids.append(field_id)
        testcase[field] = valid_ids
    testcase.save()


    return (str(mongomodifytime), 200)