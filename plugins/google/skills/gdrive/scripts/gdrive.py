#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Google Drive – read-only: list folders, download files.

Usage:
  ./gdrive.py ls <folder id|url>                 # subfolders and files: [id] type size date name
  ./gdrive.py get <folder|file id|url> <new dir> # download a file, or every non-folder file of a folder (not recursive)
"""
import io
import os
import re
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

DATA = Path(os.environ.get("GOOGLE_DATA") or "~/.config/claude-google").expanduser()
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FOLDER = "application/vnd.google-apps.folder"
ALL = dict(supportsAllDrives=True)


def creds():
    client, token = DATA / "credentials.json", DATA / "drive-token.json"
    if not client.exists():
        DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
        sys.exit(f"Missing Google OAuth client: save the downloaded Desktop-app JSON as {client} (Setup in the gsheets skill).")
    c = Credentials.from_authorized_user_file(token, SCOPES) if token.exists() else None
    if not c or not c.valid:
        if c and c.expired and c.refresh_token:
            c.refresh(Request())
        else:
            c = InstalledAppFlow.from_client_secrets_file(client, SCOPES).run_local_server(port=0)
        token.write_text(c.to_json())
        token.chmod(0o600)
    return c


def fid(s):
    m = re.search(r"/(?:folders|d)/([\w-]+)", s) or re.search(r"[?&]id=([\w-]+)", s)
    return m.group(1) if m else s


def children(api, folder):
    out, page = [], None
    while True:
        r = api.files().list(q=f"'{folder}' in parents and trashed=false", pageSize=1000, pageToken=page,
                             includeItemsFromAllDrives=True, orderBy="folder,name",
                             fields="nextPageToken,files(id,name,mimeType,size,modifiedTime)", **ALL).execute()
        out += r["files"]
        page = r.get("nextPageToken")
        if not page:
            return out


def cmd_ls(target):
    api = build("drive", "v3", credentials=creds())
    meta = api.files().get(fileId=fid(target), fields="name,owners(emailAddress)", **ALL).execute()
    print(meta["name"], f"({meta.get('owners', [{}])[0].get('emailAddress', '')})")
    for f in children(api, fid(target)):
        kind = "dir" if f["mimeType"] == FOLDER else f["mimeType"].split("/")[-1]
        print(f"  [{f['id']}] {kind:<6} {int(f.get('size', 0)) // 1024:>7} kB  {f['modifiedTime'][:10]}  {f['name']}")


def cmd_get(target, dest):
    api = build("drive", "v3", credentials=creds())
    out = Path(dest).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        sys.exit(f"{out} is not empty: downloads go to a new, empty folder.")
    meta = api.files().get(fileId=fid(target), fields="id,name,mimeType", **ALL).execute()
    files = children(api, meta["id"]) if meta["mimeType"] == FOLDER else [meta]
    for f in files:
        if f["mimeType"] == FOLDER or f["mimeType"].startswith("application/vnd.google-apps"):
            continue  # subfolders and Docs/Sheets have no binary content
        name = Path(f["name"]).name or f["id"]
        with open(out / name, "wb") as fh:
            dl = MediaIoBaseDownload(fh, api.files().get_media(fileId=f["id"], **ALL))
            done = False
            while not done:
                _, done = dl.next_chunk()
        print(out / name)


if __name__ == "__main__":
    cmds = {"ls": cmd_ls, "get": cmd_get}
    if len(sys.argv) < 3 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
