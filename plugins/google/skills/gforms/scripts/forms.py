#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Google Forms – zakládání a úprava formulářů.

Použití:
  ./forms.py list [text v názvu] [počet]   # formuláře, ke kterým mám přístup; výchozí počet 20
  ./forms.py show <id|url>                 # celý formulář jako JSON (otázky s itemId, publishSettings)
  ./forms.py create <název>                # nový prázdný nezveřejněný formulář, vypíše id a odkazy
  ./forms.py update <id|url> <requests.json|->   # batchUpdate: JSON pole requestů (nebo {"requests": [...]})
  ./forms.py publish <id|url> [off]        # zveřejnit a přijímat odpovědi / zastavit
"""
import json
import os
import re
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth client + tokens live outside any repo and survive plugin reinstalls; GOOGLE_DATA overrides
DATA = Path(os.environ.get("GOOGLE_DATA") or "~/.config/claude-google").expanduser()
SCOPES = ["https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/drive.metadata.readonly"]


def creds():
    client, token = DATA / "credentials.json", DATA / "forms-token.json"
    if not client.exists():
        DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
        sys.exit(f"Missing Google OAuth client: save the downloaded Desktop-app JSON as {client} (Setup in the gsheets skill).")
    c = None
    if token.exists() and set(SCOPES) <= set(json.loads(token.read_text()).get("scopes", [])):
        c = Credentials.from_authorized_user_file(token, SCOPES)
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            c = InstalledAppFlow.from_client_secrets_file(client, SCOPES).run_local_server(port=0)
        token.write_text(c.to_json())
        token.chmod(0o600)
    return c


def form_id(s):
    if "/forms/d/e/" in s:
        sys.exit("That is the responder link (/d/e/…). Use the edit link (/forms/d/<id>/edit) or the id from `list`.")
    m = re.search(r"/d/([\w-]+)", s)
    return m.group(1) if m else s


def forms():
    return build("forms", "v1", credentials=creds()).forms()


def cmd_list(name="", n="20"):
    q = "mimeType='application/vnd.google-apps.form' and trashed=false"
    if name:
        q += " and name contains '" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"
    files = build("drive", "v3", credentials=creds()).files().list(
        q=q, pageSize=int(n), orderBy="modifiedTime desc", fields="files(id,name,modifiedTime,owners(emailAddress))"
    ).execute()["files"]
    for f in files:
        owner = f.get("owners", [{}])[0].get("emailAddress", "")
        print(f"[{f['id']}] {f['modifiedTime'][:10]}  {f['name']}  ({owner})")


def cmd_show(fid):
    print(json.dumps(forms().get(formId=form_id(fid)).execute(), ensure_ascii=False, indent=1))


def cmd_create(title):
    f = forms().create(body={"info": {"title": title, "documentTitle": title}}).execute()
    cmd_publish(f["formId"], "off")  # new forms start published; stay closed until the user approves publishing
    print(f"[{f['formId']}] https://docs.google.com/forms/d/{f['formId']}/edit")
    print(f"responder: {f.get('responderUri', '')}")


def cmd_update(fid, path):
    body = json.load(sys.stdin if path == "-" else open(path, encoding="utf-8"))
    if isinstance(body, list):
        body = {"requests": body}
    r = forms().batchUpdate(formId=form_id(fid), body=body).execute()
    print(json.dumps(r.get("replies", []), ensure_ascii=False))


def cmd_publish(fid, state="on"):
    on = state != "off"
    s = {"publishState": {"isPublished": on, "isAcceptingResponses": on}}
    r = forms().setPublishSettings(formId=form_id(fid), body={"publishSettings": s, "updateMask": "publishState"}).execute()
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    cmds = {"list": cmd_list, "show": cmd_show, "create": cmd_create, "update": cmd_update, "publish": cmd_publish}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
