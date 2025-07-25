import secrets
from model import *
from time import time
from copy import deepcopy
from utils import user_assigned_assessment
from flask_security import auth_required, roles_accepted, current_user
from blueprints.assessment_export import exportnavigator
from flask import Blueprint, render_template, request, send_from_directory, make_response, jsonify

blueprint_assessment_utils = Blueprint('blueprint_assessment_utils', __name__)

@blueprint_assessment_utils.route('/assessment/<id>/multi/<field>', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def assessmentmulti(id, field):
    if field not in ["sources", "targets", "tools", "controls", "tags", "preventionsources", "detectionsources"]:
        return '', 418

    assessment = Assessment.objects(id=id).first()
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404

    existing_objs = {str(o.id): o for o in assessment[field]}  # Map existing objects by ID

    for row in request.json["data"]:
        if row["id"] in existing_objs:
            obj = existing_objs[row["id"]]  # Update existing object
        else:
            obj = {
                "sources": Source(),
                "targets": Target(),
                "tools": Tool(),
                "controls": Control(),
                "tags": Tag(),
                "preventionsources": Preventionsource(),
                "detectionsources": Detectionsource(),
            }[field]  # Create new object if ID not found

        obj.name = row["name"]
        if field == "tags":
            obj.colour = row["colour"]
        else:
            obj.description = row["description"]

        if row["id"] not in existing_objs:
            assessment[field].append(obj)  # Append new object instead of replacing the list

    assessment.save()

    return jsonify(assessment.multi_to_json(field)), 200

@blueprint_assessment_utils.route('/assessment/<id>/navigator', methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmentnavigator(id):
    assessment = Assessment.objects(id=id).first()

    # Create and store one-time secret; timestamp and ip for later comparison in the unauthed navigator.json endpoint
    secret = secrets.token_urlsafe()
    assessment.navigatorexport = f"{int(time())}|{request.remote_addr}|{secret}"
    assessment.save()

    exportnavigator(id)

    return render_template('assessment_navigator.html', assessment=assessment, secret=secret)

@blueprint_assessment_utils.route('/assessment/<id>/navigator.json', methods = ['GET'])
def assessmentnavigatorjson(id):
    assessment = Assessment.objects(id=id).first()
    if not assessment or not assessment.navigatorexport:
        return "", 401

    try:
        timestamp, ip, secret = assessment.navigatorexport.split("|")
    except ValueError:
        return "", 401

    request_ip = request.remote_addr
    request_secret = request.args.get("secret", type=str)
    request_origin = request.headers.get("Origin")

    # Validate conditions
    if (
        int(time()) - int(timestamp) <= 10 and
        request_ip == ip and
        request_secret == secret and
        request_origin == "https://mitre-attack.github.io"
    ):
        response = make_response(send_from_directory('files', f"{id}/navigator.json"))
        response.headers.add('Access-Control-Allow-Origin', '*')
        
        # Clear the one-time secret to prevent reuse
        assessment.navigatorexport = None
        assessment.save()

        return response

    return "", 401

@blueprint_assessment_utils.route('/assessment/<id>/stats',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmentstats(id):
    assessment = Assessment.objects(id=id).first()
    if current_user.has_role("Blue"):
        testcases = TestCase.objects(assessmentid=str(assessment.id), visible=True, deleted=False).all()
    else:
        testcases = TestCase.objects(assessmentid=str(assessment.id), deleted=False).all()

    # Initalise metrics that are captured
    stats = {
        "All": {
            "Prevented and Alerted": 0, "Prevented": 0, "Alerted": 0, "Logged": 0, "Missed": 0,
            "Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Informational": 0,
            "scoresPrevent": [], "scoresDetect": [],
            "priorityType": [], "priorityUrgency": [],
            "controls": []
        }
    }

    # What MITRE tactics do we currently have data for?
    activeTactics = list(set([t["tactic"] for t in testcases if t["state"] == "Complete"]))

    for testcase in testcases:
        if testcase["tactic"] in activeTactics:
            # Initalise tactic if not in the dataframe yet
            if testcase["tactic"] not in stats:
                stats[testcase["tactic"]] = deepcopy(stats["All"])

            # Populate prevented/alerted/logged/missed stats
            if testcase["outcome"]:
                stats[testcase["tactic"]][testcase["outcome"]] += 1

            # Populate alert severities
            if testcase["alertseverity"]:
                stats[testcase["tactic"]][testcase["alertseverity"]] += 1

            # Store scores to later average with
            if testcase["preventedrating"] and testcase["preventedrating"] != "N/A":
                stats[testcase["tactic"]]["scoresPrevent"].append(float(testcase["preventedrating"]))
            if testcase["detectionrating"]:
                stats[testcase["tactic"]]["scoresDetect"].append(float(testcase["detectionrating"]))

            # Collate priorities, ratings and controls
            if testcase["priority"] and testcase["priority"] != "N/A":
                stats[testcase["tactic"]]["priorityType"].append(testcase["priority"])
            if testcase["priorityurgency"] and testcase["priorityurgency"] != "N/A":
                stats[testcase["tactic"]]["priorityUrgency"].append(testcase["priorityurgency"])
            if testcase["controls"]:
                controls = []
                for control in testcase["controls"]:
                    controls.append([c.name for c in assessment.controls if str(c.id) == control][0])
                stats[testcase["tactic"]]["controls"].extend(controls)

    # We've populated per-tactic data, this function adds it all together for an "All" tactic
    for tactic in stats:
        if tactic == "All":
            continue
        for key in ["Prevented and Alerted", "Prevented", "Alerted", "Logged", "Missed", "Critical", "High", "Medium", "Low", "Informational"]:
            stats["All"][key] += stats[tactic][key]
        for key in ["scoresPrevent", "scoresDetect", "priorityType", "priorityUrgency", "controls"]:
            stats["All"][key].extend(stats[tactic][key])

    return render_template(
        'assessment_stats.html',
        assessment=assessment,
        stats=stats,
        hexagons=assessmenthexagons(id)
    ) 

@blueprint_assessment_utils.route('/assessment/<id>/assessment_hexagons.svg',methods = ['GET'])
@auth_required()
@user_assigned_assessment
def assessmenthexagons(id):
    # Use SVG to create the hexagon graph because making a hex grid in HTML is a no. Note this are not all, not sure why those have been choosen maybe bcs. they fit the killchain
    tactics = [ "Execution", "Command and Control", "Discovery", "Persistence", "Privilege Escalation", "Credential Access", "Lateral Movement", "Exfiltration", "Impact"]

    shownHexs = []
    hiddenHexs = []
    for i in range(len(tactics)):
        if not TestCase.objects(assessmentid=id, tactic=tactics[i], state="Complete", deleted=False).count():
            hiddenHexs.append({
                "display": "none",
                "stroke": "none",
                "fill": "none",
                "arrow": "none",
                "text": ""
            })
            continue
        
        cumulatedscore = 0
        count = 0

        for testcase in TestCase.objects(assessmentid=id, tactic=tactics[i], deleted=False):
            if testcase.testcasescore is not None:
                cumulatedscore += testcase.testcasescore
                count += 1

        if count is not 0:
            score = cumulatedscore / count

            if score == 100:
                color = "#B8DF43"
            elif score == 0:
                color = "#FB6B64"
            else:
                color = "#FFC000"

            shownHexs.append({
                "display": "block",
                "stroke": color,
                "fill": "#eeeeee",
                "arrow": "#593196",
                "text": tactics[i]
            })
        else:
            hiddenHexs.append({
                "display": "none",
                "stroke": "none",
                "fill": "none",
                "arrow": "none",
                "text": ""
            })


    # Dynamic SVG height and width depending on # hexs as CSS has no visibility
    # over which hexs are shown so we can center it for prettyness
    if len(shownHexs) == 0:
        height = 0
    if len(shownHexs) <= 4:
        height = 115
    elif len(shownHexs) <= 7:
        height = 230
    else:
        height = 347

    if len(shownHexs) == 0:
        width = 0
    if len(shownHexs) == 1:
        width = 100
    elif len(shownHexs) == 2:
        width = 240
    elif len(shownHexs) == 3:
        width = 380
    else:
        width = 517
        
    return render_template('assessment_hexagons.svg', hexs = [*shownHexs, *hiddenHexs], height = height, width = width)