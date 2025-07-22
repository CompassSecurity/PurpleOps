import pytest
import os
import json
import pymongo
import purpleops
import re
import random
import string

def generate_random_string():
    characters = string.ascii_letters + string.digits + '._-'
    random_string = ''.join(random.choice(characters) for _ in range(random.randint(5, 32)))
    return random_string


@pytest.fixture(scope="session")
def app():
    """Flask test client fixture with a mock database."""
    purpleops.app.config.update({
        "TESTING": True
    })
    yield purpleops.app

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()

@pytest.fixture
def authenticated_admin_client(client):
    """
    Logs in and returns a client with an active admin session.
    """
    # Get CSRF token
    response = client.get("/login")
    assert response.status_code == 200

    html = response.get_data(as_text=True)

    # Extract CSRF token from a <meta> tag
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match is not None, "CSRF token not found in HTML"
    csrf_token = match.group(1)

    login_data = {
        "next": "%2F",
        "email": "admin@purpleops.com",
        "password": "a9255b5f-8e9e-40c0-9815-234bf38da6d9",
        "submit": "login",
        "csrf_token": csrf_token
    }

    response = client.post(
        "/login",
        data=login_data,  # `data=` sends form-urlencoded data
        content_type="application/x-www-form-urlencoded",  # Explicitly set content type
    )

    # Ensure login was successful
    assert response.status_code == 302

    # Return the client with an active session
    return client, csrf_token

@pytest.fixture
def created_sample_user(authenticated_admin_client):
    client, csrf_token = authenticated_admin_client

    random_name = generate_random_string()
    email = random_name + "@purpleops.com"


    user_data = {
        "email": email,
        "username": random_name,
        "password": "securepass",
        "roles": "Blue",
        "assessments": [],
        "csrf_token": csrf_token
    }

    response = client.post(
        "/manage/access/user",
        data = user_data,
        content_type = "application/x-www-form-urlencoded"
    )

    assert response.status_code == 200

    # Parse JSON response
    json_data = response.get_json()
    user_id = json_data["id"]  # adjust this key based on your actual response

    return user_id

@pytest.fixture
def created_sample_assessment(authenticated_admin_client):
    client, csrf_token = authenticated_admin_client

    name = generate_random_string()
    description = generate_random_string()

    response = client.post(
        "/assessment",
        data={
            "name":name,
            "description":description,
            "csrf_token": csrf_token
        },
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 200

    # Parse JSON response
    json_data = response.get_json()
    assessment_id = json_data["id"]

    return assessment_id

@pytest.fixture
def created_sample_testcase(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    name = generate_random_string()

    form_data = {
        "name": name,
        "mitreid": "T1001.001",
        "tactic": "Execution",
        "csrf_token": csrf_token
    }

    response = client.post(
        f"/testcase/{created_sample_assessment}/single",
        data=form_data,
        content_type="application/x-www-form-urlencoded",
    )


    # Parse JSON response
    json_data = response.get_json()
    testcase_id = json_data["id"]
    assessment_id = json_data["assessmentid"]

    create_testcase_history(client, csrf_token, testcase_id)

    return assessment_id, testcase_id

def delete_assessment(client, csrf_token, assessment_id):
    headers = {
        "X-CSRFToken": csrf_token
    }
    response = client.delete(f"/assessment/{assessment_id}", headers=headers)

    assert response.status_code == 200

def delete_user(client, csrf_token, user_id):
    response = client.delete(
    f"/manage/access/user/{user_id}",
    data={"csrf_token": csrf_token},
    content_type="application/x-www-form-urlencoded"
    )

    assert response.status_code == 200

def create_testcase_history(client, csrf_token, testcase_id):

    name = generate_random_string()

    data = {
        "name": name,
        "uuid": "new-uuid",
        "state": "Waiting Blue",
        "csrf_token": csrf_token
    }

    response = client.post(f"/testcase/{testcase_id}", data=data)
    assert response.status_code == 200