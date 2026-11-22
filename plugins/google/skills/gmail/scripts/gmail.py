#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Gmail – čtení a odesílání e-mailů.

Použití:
  ./gmail.py list [počet] [gmail dotaz]   # výchozí: 10, "in:inbox"
  ./gmail.py read <id>                    # celý e-mail (id z výpisu list)
  ./gmail.py send <komu> <předmět> [bcc,bcc,...] < tělo.txt
"""
import base64
import email
import email.policy
import json
import os
import re
import sys
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth client + tokens live outside any repo and survive plugin reinstalls; GOOGLE_DATA overrides
DATA = Path(os.environ.get("GOOGLE_DATA") or "~/.config/claude-google").expanduser()
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]


def service():
    client, token = DATA / "credentials.json", DATA / "gmail-token.json"
    if not client.exists():
        sys.exit(f"Chybí OAuth klient {client} – viz Setup v SKILL.md skillu gsheets/gmail.")
    creds = None
    # starý token bez nových scopes → znovu přihlásit
    if token.exists() and set(SCOPES) <= set(json.loads(token.read_text()).get("scopes", [])):
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = InstalledAppFlow.from_client_secrets_file(client, SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
        token.chmod(0o600)
    return build("gmail", "v1", credentials=creds).users().messages()


def cmd_list(n="10", q="in:inbox"):
    gm = service()
    for m in gm.list(userId="me", q=q, maxResults=int(n)).execute().get("messages", []):
        msg = gm.get(userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
        h = {x["name"]: x["value"] for x in msg["payload"]["headers"]}
        print(f"[{m['id']}] {h.get('Date', '')}\n  {h.get('From', '')}\n  {h.get('Subject', '(bez předmětu)')}\n  {msg['snippet'][:120]}\n")


def cmd_read(msg_id):
    raw = service().get(userId="me", id=msg_id, format="raw").execute()["raw"]
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw), policy=email.policy.default)
    for k in ("From", "To", "Cc", "Date", "Subject"):
        if msg[k]:
            print(f"{k}: {msg[k]}")
    body = msg.get_body(("plain", "html"))
    print("\n" + (body.get_content() if body else "(bez textu)"))
    attachments = [a.get_filename() for a in msg.iter_attachments() if a.get_filename()]
    if attachments:
        print("\nPřílohy:", ", ".join(attachments))


def cmd_send(to, subject, bcc=""):
    msg = EmailMessage()
    msg["To"], msg["Subject"] = to, subject
    if bcc:  # čárkami oddělené adresy; Gmail hlavičku Bcc příjemcům nedoručí
        msg["Bcc"] = bcc
    body = sys.stdin.read()
    if body.lstrip().startswith("<"):  # HTML tělo + textová verze pro klienty bez HTML
        msg.set_content(re.sub(r"\n{3,}", "\n\n", re.sub(r"<[^>]+>", "", body)).strip())
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    print("Odesláno, id:", service().send(userId="me", body={"raw": raw}).execute()["id"])


if __name__ == "__main__":
    cmds = {"list": cmd_list, "read": cmd_read, "send": cmd_send}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
