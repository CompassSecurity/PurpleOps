import os
import re
import sys
import yaml
import uuid
import shutil
import dotenv
import secrets
import requests
import passlib.totp
from model import *
from git import Repo
from glob import glob
from flask import Flask
from openpyxl import load_workbook
import markdown
import bleach
import json
import mongoengine as me

dotenvFile = dotenv.find_dotenv()
dotenv.load_dotenv(dotenvFile)

PWD = os.getcwd()

app = Flask(__name__)
app.config.from_pyfile("flask.cfg")
me.connect(**app.config["MONGODB_SETTINGS"])

if not os.path.exists(f"{PWD}/external/"):
    os.makedirs(f"{PWD}/external")

MITRE_JSON_PATH = os.path.join(f"{PWD}/external/mitre", "mitre-enterprise.json")

###

def downloadMitreAttackJson():
    """Downloads the MITRE ATT&CK Enterprise JSON and saves it to /external/."""
    MITRE_JSON_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

    if os.path.exists(f"{PWD}/external/mitre"):
        shutil.rmtree(f"{PWD}/external/mitre")

    os.makedirs(f"{PWD}/external/mitre")

    try:
        response = requests.get(MITRE_JSON_URL)
        response.raise_for_status()

        with open(MITRE_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, indent=2)

    except requests.RequestException as e:
        print(f"Failed to download MITRE data: {e}")
        sys.exit(1)


def loadMitreJsonFromDisk():
    """Loads the MITRE JSON file from /external/."""
    if not os.path.exists(MITRE_JSON_PATH):
        print(f"Missing file: {MITRE_JSON_PATH}. Run downloadMitreAttackJson() first.")
        sys.exit(1)

    with open(MITRE_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parseMitreTactics():
    """Parses and saves MITRE Tactics from STIX bundle."""
    data = loadMitreJsonFromDisk()
    for obj in data.get("objects", []):
        if obj.get("type") == "x-mitre-tactic":
            Tactic(
                mitreid=obj.get("external_references", [{}])[0].get("external_id", ""),
                name=obj.get("name", "")
            ).save()


def parseMitreTechniques():
    """Parse and save MITRE techniques and sub-techniques."""
    data = loadMitreJsonFromDisk()
    for obj in data.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue

        mitre_id = obj.get("external_references", [{}])[0].get("external_id", "")
        name = obj.get("name", "")
        description = obj.get("description", "")
        detection = obj.get("x_mitre_detection", "Missing data.")
        tactics = obj.get("kill_chain_phases", [])
        tactic_names = [phase.get("phase_name") for phase in tactics if phase.get("kill_chain_name") == "mitre-attack"]

        Technique(
            mitreid=mitre_id,
            name=name,
            description=description,
            detection=detection,
            tactics=tactic_names
        ).save()

        KnowlegeBase(
            mitreid=mitre_id,
            overview=description,
            advice=detection,
            provider="MITRE"
        ).save()


def pullSigma ():
    if os.path.exists(f"{PWD}/external/sigma") and os.path.isdir(f"{PWD}/external/sigma"):
        shutil.rmtree(f"{PWD}/external/sigma")
    Repo.clone_from("https://github.com/SigmaHQ/sigma", f"{PWD}/external/sigma", depth=1)

def parseSigma ():
    pullSigma()
    for sigmaRule in glob(f'{PWD}/external/sigma/rules/**/*.yml', recursive=True):
        with open(sigmaRule, "r") as sigmaFile:
            yml = yaml.safe_load(sigmaFile)

        url = "https://github.com/SigmaHQ/sigma/blob/master/rules"
        url += sigmaRule.replace(f"{PWD}/external/sigma/rules", "")

        # ART stores relevant MitreIDs in tags, parse them out
        associatedTTP = []
        if "tags" in yml:
            for tag in yml["tags"]:
                search = re.search(r'attack\.([tT]\d\d\d\d(\.\d\d\d)*)', tag)
                if search:
                    associatedTTP.append(search.group(1).upper())

        for ttp in associatedTTP:
            Sigma(
                mitreid = ttp,
                name = yml["title"],
                description = yml["description"],
                url=url
            ).save()

def pullAtomicRedTeam ():
    if os.path.exists(f"{PWD}/external/art") and os.path.isdir(f"{PWD}/external/art"):
        shutil.rmtree(f"{PWD}/external/art")
    Repo.clone_from("https://github.com/redcanaryco/atomic-red-team", f"{PWD}/external/art", depth=1)

def parseAtomicRedTeam ():
    pullAtomicRedTeam()
    for artTestcases in glob(f'{PWD}/external/art/atomics/T*/*.yaml', recursive=True):
        with open(artTestcases, "r") as artFile:
            yml = yaml.safe_load(artFile)
            
        for artTestcase in yml["atomic_tests"]:
            # If there's no command, then we don't want it
            if "command" in artTestcase["executor"]:
                baseCommand = artTestcase["executor"]["command"].strip()
                # If there's variables in the command, populate it with the
                # default sample variables e.g. #{dumpname} > lsass.dmp
                if "input_arguments" in artTestcase and isinstance(artTestcase["input_arguments"], dict):
                    for i in artTestcase["input_arguments"].keys():
                        k = "#{" + i + "}"
                        baseCommand = baseCommand.replace(k, str(artTestcase["input_arguments"][i]["default"]))
                
                TestCaseTemplate(
                    name = artTestcase["name"],
                    mitreid = yml["attack_technique"],
                    # Infer the relevant tactic from the first match from MITRE techniques
                    tactic = Technique.objects(mitreid=yml["attack_technique"]).first()["tactics"][0],
                    objective = artTestcase["description"],
                    actions = baseCommand,
                    provider = "ART"
                ).save()

def parseCustomTestcases ():
    for customTestcase in glob(f'{PWD}/custom/testcases/**/*.yaml', recursive=True):
        with open(customTestcase, "r") as customTestcaseFile:
            yml = yaml.safe_load(customTestcaseFile)

        TestCaseTemplate(
            name = yml["name"],
            mitreid = yml["mitreid"],
            tactic = yml["tactic"],
            objective = yml["objective"],
            actions = yml["actions"],
            provider = yml["provider"],
            expectedprevention = yml["expectedprevention"],
            expectedalertcreation = yml["expectedalertcreation"],
            priorityurgency = yml["priorityurgency"],
            expectedseverity = yml["expectedseverity"],
            requirements = yml["requirements"]
        ).save()

def parseCustomKBs ():
    for customKB in glob(f'{PWD}/custom/knowledgebase/*.yaml'):
        with open(customKB, "r") as customKBFile:
            yml = yaml.safe_load(customKBFile)

        # Overwrite the reporting KB for the mitre id with the custom writeup
        KB = KnowlegeBase.objects(mitreid=yml["mitreid"]).first()
        KB.overview = yml["overview"]
        KB.advice = yml["advice"]
        KB.provider = yml["provider"]
        KB.save()

def parseCustomTestcaseKBs():
  for customtestcasekb in glob(f'{PWD}/custom/testcaseskb/*.md'):
    try:
      with open(customtestcasekb, "r") as customtestcaseKBFile:
        text = customtestcaseKBFile.read()
        escapedtext = bleach.clean(text)

        md = markdown.Markdown(extensions=['meta', 'nl2br', 'pymdownx.superfences','pymdownx.details','pymdownx.blocks.tab'])
        html = md.convert(escapedtext)
        if not "mitreid" in md.Meta:
            raise ValueError(f"File '{customtestcasekb}' is missing mitreid metadata. Skipped.")

      TestcaseKnowlegeBase(
          mitreid=md.Meta["mitreid"][0],
          mdtext=html,
      ).save()
    except ValueError as e:
      print(e)


def prepareRolesAndAdmin ():
    if Role.objects().count() == 0:
        for role in ["Admin", "Red", "Blue", "Spectator"]:
            roleObj = Role(name=role)
            roleObj.save()
    
    if User.objects().count() == 0:
        password = str(uuid.uuid4())
        dotenv.set_key(dotenvFile, "POPS_ADMIN_PWD", password)
        # TODO set to invalid email
        user_datastore.create_user(
            email = 'admin@purpleops.com',
            username = 'admin',
            password = password,
            roles = [Role.objects(name="Admin").first()],
            initpwd = False
        )
        print("==============================================================\n\n\n")
        print(f"\tCreated initial admin: U: admin@purpleops.com P: {password}")
        print("\n\n\n==============================================================")

def populateSecrets ():
    if Role.objects().count() == 0:
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECURITY_PASSWORD_SALT",
            str(secrets.SystemRandom().getrandbits(128))
        )
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECRET_KEY",
            secrets.token_urlsafe()
        )
        dotenv.set_key(
            dotenvFile,
            "FLASK_SECURITY_TOTP_SECRETS",
            f"{{1: {passlib.totp.generate_secret()}}}"
        )

#####

if Tactic.objects.count() == 0:
    print("==============================================================\n\n\n")
    print(f"\t NEW INSTANCE DETECTED, LETS GET THE DATA WE NEED")
    print("\n\n\n==============================================================")
    
    Tactic.objects.delete()
    Technique.objects.delete()
    Sigma.objects.delete()
    TestCaseTemplate.objects.delete()
    KnowlegeBase.objects.delete()
    TestcaseKnowlegeBase.objects.delete()
    # Role.objects.delete()
    # User.objects.delete()

    print("Pulling MITRE JSON")
    downloadMitreAttackJson()

    print("Populating MITRE tactics")
    parseMitreTactics()

    print("Populating MITRE techniques")
    parseMitreTechniques()

    print("Pulling SIGMA detections")
    parseSigma()

    print("Pulling Atomic Red Team testcases")
    parseAtomicRedTeam()

    print("Parsing Custom testcases")
    parseCustomTestcases()

    print("Parsing Custom testcase KB")
    parseCustomTestcaseKBs()

    print("Parsing Custom KBs")
    parseCustomKBs()

    print("Populating (randomising) secrets")
    populateSecrets()

    print("Preparing roles and initial admin")
    prepareRolesAndAdmin()

else:

    print("update testcasekb")
    parseCustomTestcaseKBs()