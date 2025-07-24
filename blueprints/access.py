from model import *
from utils import applyFormData
from flask import Blueprint, redirect, request, render_template, jsonify
from flask_security import auth_required, utils, current_user, roles_accepted

blueprint_access = Blueprint('blueprint_access', __name__)

@blueprint_access.route('/password/changed', methods = ['GET'])
@auth_required()
def passwordchanged():
    current_user.initpwd = False
    current_user.save()
    return redirect("/")

@blueprint_access.route('/manage/access', methods = ['GET'])
@auth_required()
@roles_accepted('Admin')
def users():
    return render_template(
        'access.html',
        users = User.objects,
        assessments = Assessment.objects,
        roles = Role.objects
    )

@blueprint_access.route('/manage/access/user', methods = ['POST'])
@auth_required()
@roles_accepted('Admin')
def createuser():

    email = request.form['email']
    username = request.form['username']

    if user_datastore.find_user(email=email):
        return jsonify({'error': 'Email already exists'}), 400
    if user_datastore.find_user(username=username):
        return jsonify({'error': 'Username already exists'}), 400

    user = user_datastore.create_user(
        email = email,
        username = username,
        password = utils.hash_password(request.form['password']),
        roles = [Role.objects(name=role).first() for role in request.form.getlist('roles')],
        assessments = [Assessment.objects(name=assessment).first() for assessment in request.form.getlist('assessments')]
    )
    return jsonify(user.to_json()), 200

@blueprint_access.route('/manage/access/user/<id>', methods = ['POST', 'DELETE'])
@auth_required()
@roles_accepted('Admin')
def edituser(id):
    user = User.objects(id=id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'POST':
        new_email = request.form.get('email')
        new_username = request.form.get('username')

        # Check for email conflict
        if new_email and User.objects(email=new_email, id__ne=id).first():
            return jsonify({'error': 'Email already in use'}), 400

        # Check for username conflict
        if new_username and User.objects(username=new_username, id__ne=id).first():
            return jsonify({'error': 'Username already in use'}), 400

        if "password" in request.form and request.form['password'].strip():
            user.password = utils.hash_password(request.form['password'])

        user = applyFormData(user, request.form, ["username", "email"])

        # Prevent renaming built-in admin
        if user.username != "admin" and User.objects(id=id).first().username == "admin":
            user.username = "admin"

        # Update roles
        user.roles = [
            Role.objects(name=role).first()
            for role in request.form.getlist('roles')
        ]

        # Ensure admin keeps the Admin role
        if user.username == "admin" and "Admin" not in [r.name for r in user.roles]:
            user.roles.append(Role.objects(name="Admin").first())

        # Update assessments
        user.assessments = [
            Assessment.objects(name=assessment).first()
            for assessment in request.form.getlist('assessments')
        ]

        # Admins get implicit access to all assessments
        if "Admin" in [r.name for r in user.roles]:
            user.assessments = []

        user.save()
        return jsonify(user.to_json()), 200

    if request.method == 'DELETE':
        if user.username != "admin":
            user.delete()
        return "", 200