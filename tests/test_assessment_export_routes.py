import pytest
import json
from .conftest import generate_random_string, delete_assessment

def test_admin_export_assessment_json(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/json")

    assert response.status_code == 200
    assert "assessmentid" in response.get_data(as_text=True)

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_assessment_csv(authenticated_admin_client,created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/csv")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_assessment_invalid_filetype(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/pdf")
    assert response.status_code == 401

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_campaign(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/campaign")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_templates(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/templates")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_navigator(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/navigator")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_entire(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase

    response = client.get(f"/assessment/{assessment_id}/export/entire")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)

def test_admin_export_docx(authenticated_admin_client, created_sample_testcase):
    client, csrf_token = authenticated_admin_client
    assessment_id, testcase_id = created_sample_testcase    
    
    form_data = {
        "report": "compass_overview_table.docx",
        "csrf_token": csrf_token
    }

    response = client.post(
        f"/testcase/{assessment_id}/single",
        data=form_data,
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, assessment_id)