import pytest
import json
from .conftest import generate_random_string, delete_assessment

def test_admin_new_assessment(created_sample_assessment):
    response = created_sample_assessment 

def test_admin_edit_assessment(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    name = "Updated Assessment " + generate_random_string()
    description = "Updated description " + generate_random_string()

    updated_data = {
        "name": name,
        "description": description,
        "csrf_token": csrf_token
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}",
        data=updated_data,
        content_type="application/x-www-form-urlencoded"
    )

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["name"] == name
    assert json_data["description"] == description

    delete_assessment(client, csrf_token, created_sample_assessment)

def test_admin_delete_assessment(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    delete_assessment(client, csrf_token, created_sample_assessment)