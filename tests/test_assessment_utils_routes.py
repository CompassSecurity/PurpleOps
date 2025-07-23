import pytest
import json
import re
from .conftest import delete_assessment

def test_admin_create_multi_tag(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    headers = {
        "X-CSRFToken": csrf_token
    }

    data = {
        "data": [{
            "id": "new-tag-id",
            "name": "new tag",
            "colour": "#ff00ff"
        }]
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}/multi/tags",
        data=json.dumps(data),
        content_type="application/json",
        headers=headers
    )

    assert response.status_code == 200
    json_data = response.get_json()
    assert any(tag["name"] == "new tag" for tag in json_data)

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_admin_create_multi_sources(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    headers = {
        "X-CSRFToken": csrf_token
    }

    data = {
        "data": [{
            "id": "new-tag-id",
            "name": "new tag",
            "description": "description"
        }]
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}/multi/sources",
        data=json.dumps(data),
        content_type="application/json",
        headers=headers
    )

    assert response.status_code == 200
    json_data = response.get_json()
    assert any(tag["name"] == "new tag" for tag in json_data)

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_admin_assessment_multi_invalid_field(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    headers = {
        "X-CSRFToken": csrf_token
    }

    data = {
        "data": [{
            "id": "new-tag-id",
            "name": "new tag",
            "description": "description"
        }]
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}/multi/invalidfield",
        data=json.dumps(data),
        content_type="application/json",
        headers=headers
    )

    assert response.status_code == 418

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_assessment_navigator(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client
    response = client.get(f"/assessment/{created_sample_assessment}/navigator")
    
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_assessment_secret_navigator_json(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    # Call to /navigator to create secret
    response = client.get(f"/assessment/{created_sample_assessment}/navigator")
    html = response.get_data(as_text=True)

    # Extract the secret from the HTML
    match = re.search(r'secret=([a-zA-Z0-9_\-]+)', html)
    assert match, "Secret not found in navigator HTML"

    secret = match.group(1)

    headers = {
        "Origin": "https://mitre-attack.github.io"
    }

    response = client.get(
        f"/assessment/{created_sample_assessment}/navigator.json?secret={secret}",
        headers=headers
    )
    assert response.status_code == 200 

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_assessment_wrong_secret_navigator_json(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    # Simulate previous call to /navigator to create secret
    client.get(f"/assessment/{created_sample_assessment}/navigator")

    headers = {
        "Origin": "https://mitre-attack.github.io"
    }

    response = client.get(
        f"/assessment/{created_sample_assessment}/navigator.json?secret=wrongsecret",
        headers=headers
    )
    assert response.status_code == 401

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_assessment_stats(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client
    response = client.get(f"/assessment/{created_sample_assessment}/stats")
    assert response.status_code == 200 

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)

def test_assessment_hexagons(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client
    response = client.get(f"/assessment/{created_sample_assessment}/assessment_hexagons.svg")
    assert response.status_code == 200

    #Cleanup
    delete_assessment(client, csrf_token, created_sample_assessment)