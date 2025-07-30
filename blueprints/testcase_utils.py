import os
import shutil
from model import *
from utils import *
from werkzeug.utils import secure_filename
from flask import Blueprint, request, send_from_directory, jsonify, make_response
from flask_security import auth_required, roles_accepted, current_user

blueprint_testcase_utils = Blueprint('blueprint_testcase_utils', __name__)

@blueprint_testcase_utils.route('/testcase/<id>/toggle-visibility', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
@user_assigned_assessment
def toggle_visibility_flag(id):
    testcase = get_testcase_by_id(id)
    if not testcase:
        return "Test case not found", 404

    testcase.visible = not testcase.visible
    testcase.save()
    return jsonify(testcase.to_json()), 200


@blueprint_testcase_utils.route('/testcase/<id>/clone', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
@user_assigned_assessment
def clone_testcase(id):
    orig = get_testcase_by_id(id)
    if not orig:
        return "Test case not found", 404

    fields_to_copy = [
        "name", "assessmentid", "objective", "requirements", "actions", "rednotes",
        "mitreid", "tactic", "tools", "tags", "expectedprevention",
        "expectedalertcreation", "expectedincidentcreation", "expectedseverity", "priorityurgency"
    ]
    newcase = TestCase(**{field: orig[field] for field in fields_to_copy})
    newcase.name = f"{orig['name']} (Copy)"
    newcase.save()
    return jsonify(newcase.to_json()), 200


@blueprint_testcase_utils.route('/testcase/<id>/toggle-delete', methods = ['POST'])
@auth_required()
@roles_accepted('Admin', 'Red')
@user_assigned_assessment
def toggle_delete_flag(id):
    testcase = get_testcase_by_id(id)
    if not testcase:
        return "Test case not found", 404

    testcase.deleted = not testcase.deleted
    testcase.save()
    return "", 200


@blueprint_testcase_utils.route('/testcase/<id>/delete', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
@user_assigned_assessment
def delete_testcase(id):
    testcase = get_testcase_by_id(id)
    if not testcase:
        return "Test case not found", 404

    assessment = Assessment.objects(id=testcase.assessmentid).first()
    if os.path.exists(f"files/{str(assessment.id)}/{str(testcase.id)}"):
        shutil.rmtree(f"files/{str(assessment.id)}/{str(testcase.id)}")
    testcase.delete()

    return "Test case deleted", 200


@blueprint_testcase_utils.route('/testcase/<id>/evidence/<colour>/<file>', methods = ['DELETE'])
@auth_required()
@roles_accepted('Admin', 'Red', 'Blue')
@user_assigned_assessment
def delete_file(id, colour, file):
    VALID_COLOURS = {'red', 'blue'}

    if colour not in VALID_COLOURS:
        return "Invalid colour", 400
    if colour == "red" and current_user.has_role("Blue"):
        return "Invalid colour", 400
    
    testcase = get_testcase_by_id(id)
    if not testcase:
        return "Test case not found", 404

    filepath = f"files/{testcase.assessmentid}/{testcase.id}/{secure_filename(file)}"
    if os.path.isfile(filepath):
        os.remove(filepath)

    filelist = testcase.redfiles if colour == "red" else testcase.bluefiles
    updated_files = [f for f in filelist if f.name != file]

    update_field = 'redfiles' if colour == "red" else 'bluefiles'
    testcase.update(**{f"set__{update_field}": updated_files})

    return "", 204


@blueprint_testcase_utils.route('/testcase/<id>/evidence/<file>', methods=['GET'])
@auth_required()
@user_assigned_assessment
def fetch_file(id, file):
    ALLOWED_INLINE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}

    testcase = get_testcase_by_id(id)
    if not testcase:
        return "Test case not found", 404

    filename = secure_filename(file)
    folder_path = os.path.join('files', str(testcase.assessmentid), str(testcase.id))
    file_path = os.path.join(folder_path, filename)

    if not os.path.isfile(file_path):
        return "File not found", 404

    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    as_attachment = not (ext in ALLOWED_INLINE_EXTENSIONS and "download" not in request.args)

    response = make_response(send_from_directory(folder_path, filename, as_attachment=as_attachment))
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response