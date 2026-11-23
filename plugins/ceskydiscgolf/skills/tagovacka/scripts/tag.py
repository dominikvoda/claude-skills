#!/usr/bin/env python3
"""Tagovačka (tagovacka.cz) REST client, read-only. Python 3.9+, stdlib only.

CLI:  tag.py GET PATH [--out FILE]          PATH relative to /api, e.g. /manageable-tournaments
      tag.py idg <IDG uuid> <YYYY-MM-DD>    the Tagovačka tournament id of a ceskydiscgolf.cz event
      TAG_CREDS=<file> (default ~/.tagovacka.json): {"email": "...", "password": "..."}
Lib:  sys.path.insert(0, <scripts dir>); from tag import call, find_idg
"""
import datetime, json, os, sys, urllib.error, urllib.request

BASE = 'https://api-discgolf-tags.dominikvoda.com/api'
CREDS = os.path.expanduser(os.environ.get('TAG_CREDS', '~/.tagovacka.json'))
# Cloudflare in front of the API rejects urllib's default User-Agent (error 1010).
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'

_tok = None


def load_creds():
    """The file holds a plain password: create it private, keep it private (POSIX modes; Windows has none)."""
    if not os.path.exists(CREDS):
        fd = os.open(CREDS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b'{"email": "", "password": ""}\n')
        os.close(fd)
    elif os.name == 'posix' and os.stat(CREDS).st_mode & 0o077:
        os.chmod(CREDS, 0o600)
    c = json.load(open(CREDS))
    if not c.get('email') or not c.get('password'):
        raise SystemExit(f'Fill in your Tagovačka login in {CREDS} with a text editor (not in the chat), then retry.')
    return c


def _req(method, path, body=None, tok=None):
    h = {'Accept': 'application/json', 'User-Agent': UA}
    data = None
    if body is not None:
        data, h['Content-Type'] = json.dumps(body).encode(), 'application/json'
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, data, h, method=method), timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:500]


def token():
    global _tok
    if not _tok:
        c = load_creds()
        st, r = _req('POST', '/login', {'email': c['email'], 'password': c['password']})
        if st != 200:
            raise SystemExit(f'Tagovačka login failed ({st}): check {CREDS}. Not retrying.')
        _tok = r['token']
    return _tok


def call(path):
    """GET with login. Returns (status, parsed JSON or raw text)."""
    return _req('GET', path, tok=token())


def find_idg(uuid, day):
    """Tagovačka management object of the event whose idgV2Uuid is `uuid`, among the ones you manage on `day`."""
    nxt = (datetime.date.fromisoformat(day) + datetime.timedelta(days=1)).isoformat()
    st, r = call(f'/manageable-tournaments?from={day}&to={nxt}')
    if st != 200:
        raise SystemExit(f'manageable-tournaments -> {st} {r}')
    for t in r['data']:
        st, m = call(f"/tournaments/{t['id']}/management")
        if st == 200 and m.get('idgV2Uuid') == uuid:
            return m
    raise SystemExit(f'no event with idgV2Uuid {uuid} among {[t["name"] for t in r["data"]]} on {day}')


if __name__ == '__main__':
    a = sys.argv[1:]
    out = a[a.index('--out') + 1] if '--out' in a else None
    if a[:1] == ['idg'] and len(a) >= 3:
        m = find_idg(a[1], a[2])
        res = m
        print(f"tagovacka id={m['id']} {m['name']}", file=sys.stderr)
    elif a[:1] == ['GET'] and len(a) >= 2:
        st, res = call(a[1])
        print(st, file=sys.stderr)
    else:
        raise SystemExit(__doc__)
    s = json.dumps(res, ensure_ascii=False, indent=1)
    open(out, 'w').write(s) if out else print(s)
