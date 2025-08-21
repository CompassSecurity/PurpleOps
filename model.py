import datetime
import uuid
from bson.objectid import ObjectId
from markupsafe import escape
import mongoengine as me
from flask_security import UserMixin, RoleMixin, MongoEngineUserDatastore

#Alias to keep with old style that uses flask-mongoengine
db = me

class Tactic(db.Document):
    mitreid = db.StringField()
    name = db.StringField()


class Technique(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    detection = db.StringField()
    tactics = db.ListField(db.StringField())


# TODO how to generalise? 4x same object
class Source(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw),
        }


class Target(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw),
        }


class Tool(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw),
        }


class Control(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw),
        }


class Tag(db.EmbeddedDocument):
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    colour = db.StringField(default="#ff0000")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "colour": esc(self.colour, raw), # AU spelling is non-negotiable xx
        }

class Preventionsource(db.EmbeddedDocument):    
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw)
        }

class Detectionsource(db.EmbeddedDocument):    
    id = db.ObjectIdField( required=True, default=ObjectId )
    name = db.StringField()
    description = db.StringField(default="")

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw)
        }


class File(db.EmbeddedDocument):
    name = db.StringField()
    path = db.StringField()
    caption = db.StringField(default="")


class KnowlegeBase(db.Document):
    mitreid = db.StringField()
    overview = db.StringField()
    advice = db.StringField()
    provider = db.StringField()

class TestcaseKnowlegeBase(db.Document):
    mitreid = db.StringField()
    mdtext = db.StringField()

class Sigma(db.Document):
    mitreid = db.StringField()
    name = db.StringField()
    description = db.StringField()
    url = db.StringField()

class TestCaseTemplate(db.Document):
    name = db.StringField()
    mitreid = db.StringField(default="")
    tactic = db.StringField(default="")
    objective = db.StringField(default="")
    actions = db.StringField(default="")
    rednotes = db.StringField(default="")
    uuid = db.StringField(default="")
    provider = db.StringField(default="")
    expectedprevention = db.BooleanField()
    expectedalertcreation = db.BooleanField()
    expectedseverity = db.StringField(default="")
    priorityurgency = db.StringField(default="")
    requirements = db.StringField(default="")

class TestCase(db.Document):
    assessmentid = db.StringField()
    name = db.StringField()
    objective = db.StringField(default="")
    actions = db.StringField(default="")
    rednotes = db.StringField(default="")
    bluenotes = db.StringField(default="")
    uuid = db.StringField(default=lambda: str(uuid.uuid4()).upper()[:8])
    mitreid = db.StringField()
    tactic = db.StringField()
    sources = db.ListField(db.StringField())
    targets = db.ListField(db.StringField())
    tools = db.ListField(db.StringField())
    controls = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    preventionsources = db.ListField(db.StringField())
    detectionsources = db.ListField(db.StringField())
    state = db.StringField(default="Pending")
    prevented = db.BooleanField()
    preventedrating = db.StringField()
    alerted = db.BooleanField()
    alertseverity = db.StringField()
    logged = db.BooleanField()
    detectionrating = db.StringField()
    priority = db.StringField(default="Prevent and Alert")
    priorityurgency = db.StringField()
    expectedprevention = db.BooleanField(default=False)
    expectedalertcreation = db.BooleanField(default=True)
    expectedincidentcreation = db.BooleanField(default=False)
    expectedseverity = db.StringField()
    starttime = db.DateTimeField()
    endtime = db.DateTimeField()
    detecttime = db.DateTimeField()
    alerttime = db.DateTimeField()
    preventtime = db.DateTimeField()
    redfiles = db.EmbeddedDocumentListField(File)
    bluefiles = db.EmbeddedDocumentListField(File)
    visible = db.BooleanField(default=False)
    deleted = db.BooleanField(default=False)
    modifytime = db.DateTimeField(default=datetime.datetime.utcnow)
    outcome = db.StringField(default="")
    testcasescore = db.IntField()
    alertseverityscore = db.IntField()
    incidentcreated = db.BooleanField()
    incidentseverity = db.StringField()
    incidentseverityscore = db.IntField()
    incidenttime = db.DateTimeField()
    eventtoalert = db.StringField(default="")
    alerttoincident = db.StringField(default="")
    requirements = db.StringField(default="")

    def to_json(self, raw=False):
        jsonDict = {}
        for field in ["assessmentid", "name", "objective", "actions", "rednotes", "bluenotes",
                      "uuid", "mitreid", "tactic", "state", "prevented", "preventedrating",
                      "alerted", "alertseverity", "logged", "detectionrating",
                      "priority", "priorityurgency", "expectedseverity", "expectedincidentcreation", 
                      "visible", "outcome", "testcasescore", "alertseverityscore", "incidentcreated", 
                      "incidentseverity", "incidentseverityscore", "eventtoalert", "alerttoincident", "expectedprevention", "expectedalertcreation","requirements" ]:
            jsonDict[field] = esc(self[field], raw)
        for field in ["id", "detecttime", "modifytime", "starttime", "endtime", "alerttime", "preventtime", "incidenttime"]:
            jsonDict[field] = str(self[field]).split(".")[0]
        for field in ["tags", "sources", "targets", "tools", "controls", "preventionsources", "detectionsources"]:
            jsonDict[field] = self.to_json_multi(field)
        for field in ["redfiles", "bluefiles"]:
            files = []
            for file in self[field]:
                files.append(f"{file.path}|{file.caption}")
            jsonDict[field] = files
        return jsonDict
    
    def to_json_multi(self, field):
        assessment = Assessment.objects(id=self.assessmentid).first()
        strs = []
        for i in self[field]:
            # Pipe delimit name and desc/colour for export/display
            if field != "tags":
                strs.append([f"{j.name}|{j.description}" for j in assessment[field] if str(j.id) == i][0])
            else:
                strs.append([f"{j.name}|{j.colour}" for j in assessment[field] if str(j.id) == i][0])
        return strs

class TestCaseHistory(db.Document):
    testcaseid = db.ObjectIdField(required=True)
    testcase_name = db.StringField()
    snapshot = db.DictField(required=True)
    timestamp = db.DateTimeField(default=datetime.datetime.utcnow)
    modified_by = db.StringField()
    version = db.IntField()

class Assessment(db.Document):
    name = db.StringField()
    description = db.StringField(default="")
    created = db.DateTimeField(default=datetime.datetime.utcnow)
    targets = db.EmbeddedDocumentListField(Target)
    sources = db.EmbeddedDocumentListField(Source)
    tools = db.EmbeddedDocumentListField(Tool)
    controls = db.EmbeddedDocumentListField(Control)
    tags = db.EmbeddedDocumentListField(Tag)
    preventionsources = db.EmbeddedDocumentListField(Preventionsource)
    detectionsources = db.EmbeddedDocumentListField(Detectionsource)
    navigatorexport = db.StringField(default="")

    def get_progress(self):
        # Returns string with % of "missed|logged|alerted|prevented|pending"
        testcases = TestCase.objects(assessmentid=str(self.id), deleted=False).count()
        if testcases == 0:
            return "0|0|0|0|0"
        
        scores = []
        for score in ["100", "66","50","33","0"]:
            scores.append(str(round(
                TestCase.objects(assessmentid=str(self.id), state=str("Complete"), deleted=False, testcasescore=score).count() /
                testcases * 100
                )))      
        return "|".join(scores)

    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "name": esc(self.name, raw),
            "description": esc(self.description, raw),
            "progress": self.get_progress(),
            "created": str(self.created).split(".")[0]
        }
                    
    def multi_to_json(self, field, raw=False):
        return [item.to_json(raw=raw) for item in self[field]]


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255, default="")


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255, unique=True, nullable=True)
    username = db.StringField(max_length=255, unique=True, nullable=True)
    password = db.StringField(max_length=255)
    roles = db.ListField(db.ReferenceField(Role), default=[])
    assessments = db.ListField(db.ReferenceField(Assessment), default=[])
    initpwd = db.BooleanField(default=True)
    active = db.BooleanField(default=True)

    last_login_at = db.DateTimeField()
    current_login_at = db.DateTimeField()
    last_login_ip = db.StringField()
    current_login_ip = db.StringField()
    login_count = db.IntField()

    fs_uniquifier = db.StringField(max_length=255, unique=True)
    tf_primary_method = db.StringField(max_length=64, nullable=True)
    tf_totp_secret = db.StringField(max_length=255, nullable=True)

    def assessment_list(self):
        if "Admin" in [r.name for r in self.roles]:
            return [a.id for a in Assessment.objects()]
        else:
            return [a.id for a in self.assessments]
        
    def to_json(self, raw=False):
        return {
            "id": str(self.id),
            "username": esc(self.username, raw),
            "email": esc(self.email, raw),
            "roles": [r.name for r in self.roles],
            "assessments": [a.name for a in self.assessments],
            "current_login_at": self.current_login_at,
            "current_login_ip": self.current_login_ip
        }


user_datastore = MongoEngineUserDatastore(db, User, Role)

def esc(s, raw):
    if raw:
        return s
    else:
        return escape(s)
