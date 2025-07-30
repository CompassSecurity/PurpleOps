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
def new_testcase(id):
    testcase = TestCase()
    testcase.assessmentid = id
    testcase = applyFormData(testcase, request.form, ["name", "mitreid", "tactic"])
    testcase.save()
    return jsonify(testcase.to_json()), 200


@blueprint_testcase.route('/testcase/<id>',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def render_testcase(id):
    testcase = get_testcase_by_id(id)
    if not testcase or testcase.deleted:
        return "Test case not found", 404

    if not testcase.visible and current_user.has_role("Blue"):
        return "", 403

    assessment = Assessment.objects(id=testcase.assessmentid).first()
    history_entries = TestCaseHistory.objects(testcaseid=id).order_by('-timestamp')

    return render_template('testcase.html',
        testcase = testcase,
        testcases = TestCase.objects(assessmentid=str(assessment.id)).all(),
        tactics = Tactic.objects().all(),
        assessment = assessment,
        kb = KnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        testcasekb = TestcaseKnowlegeBase.objects(mitreid=testcase.mitreid).first(),
        history_entries=history_entries,
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


@blueprint_testcase.route('/testcase/<id>',methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def save_testcase(id):
    testcase = get_testcase_by_id(id)
    if not testcase or testcase.deleted:
        return "Test case not found", 404

    is_blue = current_user.has_role("Blue")
    if not testcase.visible and is_blue:
        return "", 403

    # Access control for Blue team
    if is_blue:
        if request.form.get("state") not in ["Waiting Blue", "Waiting Red", None]:
            return "Not allowed state value", 403
        if testcase.state not in ["Waiting Blue", "Waiting Red"]:
            return "State cannot be changed at the moment", 403

    # Prevent race condition on concurrent update
    if request.form.get("modifytime") and request.form.get("modifytime") != str(testcase.modifytime):
        return "Testcase has been modified in the meantime.", 409

    # Field categories based on role
    direct_fields = ["bluenotes", "prevented", "alerted", "alertseverity", "state", "incidentcreated", "incidentseverity"] if is_blue else \
                    ["name", "objective", "actions", "rednotes", "bluenotes", "uuid", "mitreid", "tactic", "state", "preventedrating", "alertseverity", "logged", "detectionrating", "priority", "priorityurgency", "expectedseverity", "incidentseverity", "requirements"]

    list_fields = ["tags", "preventionsources", "detectionsources"] if is_blue else \
                  ["sources", "targets", "tools", "controls", "tags", "preventionsources", "detectionsources"]

    bool_fields = ["prevented", "alerted", "logged", "incidentcreated"] if is_blue else \
                  ["alerted", "logged", "visible", "incidentcreated", "prevented", "expectedincidentcreation", "expectedprevention", "expectedalertcreation"]

    time_fields = ["alerttime", "preventtime", "incidenttime"] if is_blue else \
                  ["starttime", "endtime", "alerttime", "preventtime", "incidenttime"]

    file_fields = ["bluefiles"] if is_blue else ["redfiles", "bluefiles"]

    # Apply updates
    testcase = applyFormData(testcase, request.form, direct_fields)
    testcase = applyFormListData(testcase, request.form, list_fields)
    testcase = applyFormBoolData(testcase, request.form, bool_fields)
    testcase = applyFormTimeData(testcase, request.form, time_fields)

    # File handling
    file_dir = os.path.join("files", str(testcase.assessmentid), str(testcase.id))
    os.makedirs(file_dir, exist_ok=True)

    for field in file_fields:
        updated_files = []
        for uploaded_file in request.files.getlist(field):
            if uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                file_path = os.path.join(file_dir, filename)
                if os.path.exists(file_path):
                    return f"File '{filename}' already exists.", 409
                uploaded_file.save(file_path)
                updated_files.append({"name": filename, "path": file_path, "caption": ""})

        # Preserve existing files
        for existing in getattr(testcase, field):
            caption = request.form.get(field.replace("files", "").upper() + existing.name, "")
            updated_files.append({"name": secure_filename(existing.name), "path": existing.path, "caption": caption})

        testcase.update(**{f"set__{field}": updated_files})

    testcase.modifytime = datetime.utcnow()
    if request.form.get("logged") == "Yes" and not testcase.detecttime:
        testcase.detecttime = datetime.utcnow()

    # Scoring and outcome logic
    testcase.alertseverityscore = calculate_severity_score(testcase.alertseverity, testcase.expectedseverity)
    testcase.incidentseverityscore = calculate_severity_score(testcase.incidentseverity, testcase.expectedseverity)

    if not testcase.logged:
        testcase.outcome = "Missed"
    elif testcase.prevented and testcase.alerted:
        testcase.outcome = "Prevented and Alerted"
    elif testcase.prevented:
        testcase.outcome = "Prevented"
    elif testcase.alerted:
        testcase.outcome = "Alerted"
    else:
        testcase.outcome = "Logged"

    expected_criteria = sum([
        testcase.expectedalertcreation,
        testcase.expectedprevention,
        True  # always check logged
    ])
    score_unit = 100 / expected_criteria
    testcase.testcasescore = sum([
        score_unit if testcase.logged else 0,
        score_unit if testcase.expectedalertcreation and testcase.alerted else 0,
        score_unit if testcase.expectedprevention and testcase.prevented else 0
    ])

    testcase.eventtoalert = format_time_difference(testcase.alerttime, testcase.starttime) or ""
    testcase.alerttoincident = format_time_difference(testcase.incidenttime, testcase.alerttime) or ""

    # Sanity check list fields with assessment items
    assessment = Assessment.objects(id=testcase.assessmentid).first()
    for field in list_fields:
        valid_ids = {str(item.id) for item in assessment[field]}
        testcase[field] = [id for id in testcase[field] if id in valid_ids]

    testcase.save()

    TestCaseHistory(
        testcaseid=testcase.id,
        testcase_name=testcase.name,
        snapshot=testcase.to_mongo().to_dict(),
        version=TestCaseHistory.objects(testcaseid=testcase.id).count() + 1,
        modified_by=f"{current_user.username} ({current_user.id})"
    ).save()

    return str(testcase.modifytime)[:-3] + "000", 200

@blueprint_testcase.route('/testcase/<id>/history/<int:version>', methods=['GET'])
@auth_required()
@user_assigned_assessment
def view_testcase_history_version(id, version):
    testcase = get_testcase_by_id(id)
    if not testcase or testcase.deleted:
        return "Test case not found", 404

    is_blue_or_spectator = current_user.has_role("Blue") or current_user.has_role("Spectator")
    if not testcase.visible and is_blue_or_spectator:
        return "", 403

    history = TestCaseHistory.objects(testcaseid=id, version=version).first()
    if not history:
        return "History version not found", 404

    snapshot = TestCase._from_son(history.snapshot)
    assessment = Assessment.objects(id=snapshot.assessmentid).first()

    return render_template('testcase.html',
        testcase=snapshot,
        testcases=TestCase.objects(assessmentid=str(assessment.id)).all(),
        tactics=Tactic.objects().all(),
        assessment=assessment,
        kb=KnowlegeBase.objects(mitreid=snapshot.mitreid).first(),
        testcasekb=TestcaseKnowlegeBase.objects(mitreid=snapshot.mitreid).first(),
        templates=TestCaseTemplate.objects(mitreid=snapshot.mitreid),
        mitres=[[m["mitreid"], m["name"]] for m in Technique.objects()],
        sigmas=Sigma.objects(mitreid=snapshot.mitreid),
        multi={
            "sources": assessment.sources,
            "targets": assessment.targets,
            "tools": assessment.tools,
            "controls": assessment.controls,
            "tags": assessment.tags,
            "preventionsources": assessment.preventionsources,
            "detectionsources": assessment.detectionsources
        },
        history_read_only=True,
        history_version=history.version,
        history_modified_by=history.modified_by,
        history_timestamp=history.timestamp
    )