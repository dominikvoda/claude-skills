#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Google Sheets – čtení tabulek.

Použití:
  ./sheets.py list [text v názvu] [počet]   # tabulky, ke kterým mám přístup; výchozí počet 20
  ./sheets.py tabs <id|url>                 # listy tabulky a jejich velikost
  ./sheets.py read <id|url> [rozsah]        # hodnoty jako TSV; výchozí první list, např. "List1!A1:D50"
"""
import csv
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
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.metadata.readonly"]


def creds():
    client, token = DATA / "credentials.json", DATA / "sheets-token.json"
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


def sheet_id(s):
    m = re.search(r"/d/([\w-]+)", s)
    return m.group(1) if m else s


def cmd_list(name="", n="20"):
    q = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    if name:
        q += " and name contains '" + name.replace("\\", "\\\\").replace("'", "\\'") + "'"
    files = build("drive", "v3", credentials=creds()).files().list(
        q=q, pageSize=int(n), orderBy="modifiedTime desc", fields="files(id,name,modifiedTime,owners(emailAddress))"
    ).execute()["files"]
    for f in files:
        owner = f.get("owners", [{}])[0].get("emailAddress", "")
        print(f"[{f['id']}] {f['modifiedTime'][:10]}  {f['name']}  ({owner})")


def cmd_tabs(sid):
    meta = build("sheets", "v4", credentials=creds()).spreadsheets().get(
        spreadsheetId=sheet_id(sid), fields="properties.title,sheets.properties(title,gridProperties)"
    ).execute()
    print(meta["properties"]["title"])
    for s in meta["sheets"]:
        p, g = s["properties"], s["properties"]["gridProperties"]
        print(f"  {p['title']}  ({g.get('rowCount', 0)} × {g.get('columnCount', 0)})")


def cmd_read(sid, rng=None):
    api = build("sheets", "v4", credentials=creds()).spreadsheets()
    sid = sheet_id(sid)
    if not rng:
        rng = "'" + api.get(spreadsheetId=sid, fields="sheets.properties.title").execute()["sheets"][0]["properties"]["title"] + "'"
    rows = api.values().get(spreadsheetId=sid, range=rng).execute().get("values", [])
    csv.writer(sys.stdout, delimiter="\t", lineterminator="\n").writerows(rows)


if __name__ == "__main__":
    cmds = {"list": cmd_list, "tabs": cmd_tabs, "read": cmd_read}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
