import pytest
import json
from .conftest import generate_random_string, delete_user

def test_admin_passwordchanged_route(authenticated_admin_client):
    client, csrf_token = authenticated_admin_client

    response = client.get("/password/changed")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

def test_admin_manage_access_get(authenticated_admin_client):
    client, csrf_token = authenticated_admin_client

    response = client.get("/manage/access")
    assert response.status_code == 200

def test_admin_create_user_route(authenticated_admin_client, created_sample_user):
    client, csrf_token = authenticated_admin_client
    response = created_sample_user

    #Cleanup
    delete_user(client, csrf_token, created_sample_user)

def test_admin_edit_user_post(authenticated_admin_client, created_sample_user):
    client, csrf_token = authenticated_admin_client

    random_name = generate_random_string()
    email = random_name + "@purpleops.com"

    data = {
        "username": "updateduser" + random_name,
        "email": email,
        "password": "newpassword",
        "roles": "Red",
        "assessments": [],
        "csrf_token": csrf_token
    }

    response = client.post(
        f"/manage/access/user/{created_sample_user}",
        data=data,
        content_type="application/x-www-form-urlencoded"
    )

    # Parse JSON response
    json_data = response.get_json()
    user_id = json_data["id"]

    assert response.status_code == 200
    assert email in response.get_data(as_text=True)

    #Cleanup
    delete_user(client, csrf_token, user_id)

def test_admin_user_delete(authenticated_admin_client, created_sample_user):
    client, csrf_token = authenticated_admin_client

    delete_user(client, csrf_token, created_sample_user)