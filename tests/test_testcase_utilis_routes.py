import pytest
import json
import os
from .conftest import delete_assessment


def test_admin_toggle_visibility(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.post(
        f"/testcase/{testcase_id}/toggle-visibility",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 

def test_admin_toggle_deleted(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.post(
        f"/testcase/{testcase_id}/toggle-delete",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 

def test_admin_clone_testcase(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.post(
        f"/testcase/{testcase_id}/clone",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["name"].endswith("(Copy)")

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 

def test_admin_delete_testcase(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.post(
        f"/testcase/{testcase_id}/delete",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)



def test_admin_fetch_file(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase
    file_name = "test_file.txt"

    response = client.get(
        f"/testcase/{testcase_id}/evidence/{file_name}",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200
    assert response.data.startswith(b"This is the content of the file.")

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)


def test_admin_delete_evidence_file(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase
    file_name = "test_file.txt"

    path = f"files/{assessment_id}/{testcase_id}/{file_name}"
    assert os.path.exists(path)

    response = client.delete(
        f"/testcase/{testcase_id}/evidence/red/{file_name}",
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 204
    assert not os.path.exists(path)

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)