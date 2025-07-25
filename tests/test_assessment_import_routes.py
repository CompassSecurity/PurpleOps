import pytest
import json
import io
import re
import zipfile
from .conftest import delete_assessment

@pytest.fixture
def campaign_payload():
    return [
        {
            "name": "Phishing Email",
            "mitreid": "T1566",
            "tactic": "Initial Access",
            "objective": "Gain access via email",
            "actions": "Send email",
            "tools": ["PhishTool|A phishing tool"],
            "tags": ["Phishing|#ff0000"]
        }
    ]

def test_admin_import_campaign(authenticated_admin_client, created_sample_assessment, campaign_payload):
    client, csrf_token = authenticated_admin_client

    data = {
        'file': (io.BytesIO(json.dumps(campaign_payload).encode('utf-8')), 'campaign.json')
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}/import/campaign",
        data=data,
        content_type='multipart/form-data',
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200
    assert len(response.json) == len(campaign_payload)

    delete_assessment(client, csrf_token, created_sample_assessment)

@pytest.fixture
def navigator_payload():
    return {
        "techniques": [
            {"techniqueID": "T1001", "tactic": "initial-access"},
            {"techniqueID": "T1003", "tactic": "Credential Access"}
        ]
    }

def test_admin_import_navigator(authenticated_admin_client, created_sample_assessment, navigator_payload):
    client, csrf_token = authenticated_admin_client

    data = {
        'file': (io.BytesIO(json.dumps(navigator_payload).encode('utf-8')), 'navigator.json')
    }

    response = client.post(
        f"/assessment/{created_sample_assessment}/import/navigator",
        data=data,
        content_type='multipart/form-data',
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200
    assert len(response.json) == len(navigator_payload["techniques"])

    delete_assessment(client, csrf_token, created_sample_assessment)

def test_import_template_from_html(authenticated_admin_client, created_sample_assessment):
    client, csrf_token = authenticated_admin_client

    # Get the assessment page HTML to laod existing IDs
    response = client.get(f"/assessment/{created_sample_assessment}")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # regex to find up to 3 template IDs from the table rows
    # Matches: <tr ...> ... <td>...<td>...<td>...<td>...<td>...<td>template_id</td>
    pattern = re.compile(r'<tr.*?>.*?<td>.*?</td>\s*'     # <td>Src</td>
                         r'<td>.*?</td>\s*'               # <td>Tactic</td>
                         r'<td>.*?</td>\s*'               # <td>Technique</td>
                         r'<td>.*?</td>\s*'               # <td>Title</td>
                         r'<td>(?P<id>[a-f0-9]{24})</td>', re.DOTALL)

    ids = [match.group("id") for match in pattern.finditer(html)]
    ids = ids[:3]  # Use up to 3

    assert ids, "No template IDs found in HTML."

    # Send the import request
    post_response = client.post(
        f"/assessment/{created_sample_assessment}/import/template",
        json={"ids": ids},
        headers={"X-CSRFToken": csrf_token},
    )

    assert post_response.status_code == 200
    assert len(post_response.json) == len(ids)

    delete_assessment(client, csrf_token, created_sample_assessment)

@pytest.fixture
def sample_entire_export_zip(tmp_path):
    zip_dir = tmp_path / "export"
    zip_dir.mkdir(parents=True)
    
    # Create minimal export.json
    export_data = [{
        "name": "TC1",
        "objective": "Obj",
        "actions": "Act",
        "uuid": "abc",
        "mitreid": "T1001",
        "tactic": "Execution",
        "sources": [],
        "targets": [],
        "tools": [],
        "controls": [],
        "tags": [],
        "preventionsources": [],
        "detectionsources": [],
        "redfiles": [],
        "bluefiles": [],
        "starttime": "None",
        "endtime": "None",
        "detecttime": "None",
        "modifytime": "None",
        "alerttime": "None",
        "preventtime": "None",
        "incidenttime": "None"
    }]
    with open(zip_dir / "export.json", "w") as f:
        json.dump(export_data, f)

    # Create meta.json
    with open(zip_dir / "meta.json", "w") as f:
        json.dump({"name": "Imported Assessment", "description": "From zip"}, f)

    # Zip it
    zip_path = tmp_path / "entire.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(zip_dir / "export.json", "export.json")
        zf.write(zip_dir / "meta.json", "meta.json")

    return zip_path.read_bytes()

def test_admin_import_entire(authenticated_admin_client, sample_entire_export_zip):
    client, csrf_token = authenticated_admin_client

    data = {
        'file': (io.BytesIO(sample_entire_export_zip), 'entire.zip')
    }

    response = client.post(
        "/assessment/import/entire",
        data=data,
        content_type='multipart/form-data',
        headers={"X-CSRFToken": csrf_token},
    )

    assert response.status_code == 200
    assert "name" in response.json
    assert "description" in response.json

    json_data = response.get_json()
    assessment_id = json_data["id"]

    delete_assessment(client, csrf_token, assessment_id)