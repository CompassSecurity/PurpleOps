import pytest
import re
import json

def get_csrf_token(response_data):
    """Extract CSRF token from the <meta> tag in the HTML response."""
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', response_data)
    if match:
        return match.group(1)
    raise ValueError("CSRF token not found in response")

@pytest.fixture
def authenticated_admin_client(client):
    """
    Logs in and returns a client with an active admin session.
    """
    # Get CSRF token
    response = client.get("/login")
    csrf_token = get_csrf_token(response.get_data(as_text=True))

    login_data = {
        "next": "%2F",
        "email": "admin@purpleops.com",
        "password": "0e6ec131-5371-4d6f-8f85-23da4171c7a1",
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

    # Step 3: Return the client with an active session
    return client


def test_check_status(client):
    """Test if app is running"""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"<title>PurpleOps</title>" in response.data

def test_access_assessment_admin(authenticated_admin_client):
    """Ensure an authenticated user can access an existing assessment."""
    response = authenticated_admin_client.get("/assessment/67e111dd4d88275628a1184a")
    assert response.status_code == 200

def test_create_new_assessment_admin(authenticated_admin_client):
    """Ensure an authenticated admin user can create a new assessment"""
    # Get CSRF token
    response = authenticated_admin_client.get("/")
    csrf_token = get_csrf_token(response.get_data(as_text=True))


    # POST data
    form_data = {
        "name": "new assessment",
        "description": "created by pytest",
        "csrf_token": csrf_token
    }

    response = authenticated_admin_client.post(
        "/assessment",
        data=form_data,
        content_type="application/x-www-form-urlencoded",
    )

    # Assert the response
    response_json = response.get_json()  # Parse the JSON response

    assert response.status_code == 200

    assert response_json["name"] == "new assessment", "Wrong content in 'name' field"
    assert response_json["description"] == "created by pytest", "Wrong content in 'description' field"

    # Assert specific keys and values within the response body
    assert "created" in response_json, "Missing 'created' key in response"
    assert "id" in response_json, "Missing 'id' key in response"
    assert "progress" in response_json, "Missing 'progress' key in response"
    
def test_access_testcase_admin(authenticated_admin_client):
    """Test if authenticated admin user can access a testcase"""
    response = authenticated_admin_client.get("/testcase/67e14b2ec6de8c33f6c90392")
    assert response.status_code == 200
    assert b"test rednotes" in response.data


def test_create_new_testcase_admin(authenticated_admin_client):
    """Ensure an authenticated admin user can create a new testcase"""
    # Get CSRF token
    response = authenticated_admin_client.get("/assessment/67e111dd4d88275628a1184a")
    csrf_token = get_csrf_token(response.get_data(as_text=True))


    # POST data
    form_data = {
        "name": "new testcase",
        "mitreid": "T1001.001",
        "tactic": "Execution",
        "csrf_token": csrf_token
    }

    response = authenticated_admin_client.post(
        "/testcase/67e111dd4d88275628a1184a/single",
        data=form_data,
        content_type="application/x-www-form-urlencoded",
    )

    # Assert the response
    response_json = response.get_json()  # Parse the JSON response

    assert response.status_code == 200

    assert response_json["name"] == "new testcase", "Wrong content in 'name' field"
    assert response_json["mitreid"] == "T1001.001", "Wrong content in 'mitreid' field"

    # Assert specific keys and values within the response body
    assert "uuid" in response_json, "Missing 'uuid' key in response"
    assert "id" in response_json, "Missing 'id' key in response"