from datetime import datetime, timedelta
from model import TestCase
from flask_security import current_user
from functools import wraps
from mongoengine.errors import ValidationError

def applyFormData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form[field]
    return obj

def applyFormListData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form.getlist(field)
    return obj

def applyFormBoolData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            obj[field] = form[field].lower() in ["true", "yes", "on"]
    return obj

def applyFormTimeData (obj, form, fields):
    for field in fields:
        if field in form: # and form[field]:
            if form[field] and form[field] != "None":
                utcTime = datetime.strptime(form[field], "%Y-%m-%dT%H:%M")
                # utcTime = localTime + timedelta(minutes=int(form["timezone"]))
                obj[field] = utcTime
            else:
                obj[field] = None
    return obj

def get_testcase_by_id(id):
    try:
        return TestCase.objects(id=id).first()
    except ValidationError:
        return None

def format_time_difference(d1, d2):

    if not d1 or not d2:
        return None

    if d2 > d1:
        return None

    delta = abs(d1-d2)

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")

    return  " ".join(parts)

def calculate_severity_score(severity, expected_severity):
    severity_levels = {
        "Critical": ["Critical"],
        "High": ["Critical", "High"],
        "Medium": ["Critical", "High", "Medium"],
        "Low": ["Critical", "High", "Medium", "Low"],
        "Informational": ["Critical", "High", "Medium", "Low", "Informational"]
    }
    if severity and expected_severity:
        accepted_severity_list = severity_levels.get(expected_severity, [])
        return 100 if severity in accepted_severity_list else 0
    return None

def user_assigned_assessment(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if current_user.has_role("Admin"):
            return f(*args, **kwargs)

        id = kwargs.get("id") or (args[0] if args else None)
        if not id:
            return ("Missing ID", 400)

        testcase = get_testcase_by_id(id)
        if testcase:
            assessment_id = str(testcase.assessmentid)
        else:
            assessment_id = id  # fallback to assuming it's already an assessment ID

        if assessment_id in [str(a.id) for a in current_user.assessments]:
            return f(*args, **kwargs)
        else:
            current_app.logger.warning(f"Access denied for user {current_user.id} on assessment {assessment_id}")
            return ("", 403)

    return inner