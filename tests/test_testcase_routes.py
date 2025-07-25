import pytest
import json
from .conftest import delete_assessment

def test_admin_get_testcase(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/testcase/{testcase_id}")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_save_testcase(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    data = {
        "name": "Updated Test Case",
        "uuid": "new-uuid",
        "state": "Waiting Blue",
        "csrf_token": csrf_token
    }

    response = client.post(f"/testcase/{testcase_id}", data=data)
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 

def test_view_testcase_history(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/testcase/{testcase_id}/history/1")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 

def test_view_testcase_history_not_found(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/testcase/{testcase_id}/history/999")
    assert response.status_code == 404

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id) 