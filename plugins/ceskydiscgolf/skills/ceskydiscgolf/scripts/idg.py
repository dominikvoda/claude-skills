#!/usr/bin/env python3
"""ceskydiscgolf.cz (iDiscGolf v2) REST client. Python 3.9+, stdlib only.

CLI:  idg.py METHOD PATH [JSON_BODY] [--auth] [--pii] [--out FILE]
      IDG_HOST=<api host> targets another server (default prod). Prod non-GET needs PROD_GO=1.
      IDG_CREDS=<file> (default ~/.ceskydiscgolf.json): {"username": "...", "password": "..."}
      GET is anonymous unless --auth; writes always authenticate.
      e-mail/phone fields are stripped unless --pii.
Lib:  sys.path.insert(0, <scripts dir>); from idg import call
"""
import json, os, sys, urllib.error, urllib.request

PROD = 'https://api.ceskydiscgolf.cz'
HOST = os.environ.get('IDG_HOST', PROD).rstrip('/')
ENV = 'prod' if HOST == PROD else 'staging'  # any non-prod host counts as staging
BASE = HOST + '/api'
CREDS = os.path.expanduser(os.environ.get('IDG_CREDS', '~/.ceskydiscgolf.json'))
PII = ('email', 'phone', 'user_email', 'user_phone', 'bank_account_number')

_tok = None


def load_creds():
    """The file holds a plain password: create it private, keep it private (POSIX modes; Windows has none)."""
    if not os.path.exists(CREDS):
        fd = os.open(CREDS, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b'{"username": "", "password": ""}\n')
        os.close(fd)
    elif os.name == 'posix' and os.stat(CREDS).st_mode & 0o077:
        os.chmod(CREDS, 0o600)
    c = json.load(open(CREDS))
    if not (c.get('username') or c.get('email')) or not c.get('password'):
        raise SystemExit(f'Fill in your ceskydiscgolf.cz login in {CREDS} with a text editor (not in the chat), then retry.')
    return c


def token():
    global _tok
    if not _tok:
        c = load_creds()
        body = json.dumps({'username': c.get('username') or c.get('email'), 'password': c['password']}).encode()
        req = urllib.request.Request(BASE + '/user/token/', body, {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            _tok = json.loads(r.read())['access']
    return _tok


def strip_pii(o):
    if isinstance(o, dict):
        return {k: strip_pii(v) for k, v in o.items() if k not in PII}
    if isinstance(o, list):
        return [strip_pii(x) for x in o]
    return o


def call(method, path, body=None, auth=None, pii=False, timeout=90):
    """Returns (status, parsed JSON or raw text). path is relative to /api, keep the trailing slash."""
    method = method.upper()
    if ENV == 'prod' and method != 'GET' and os.environ.get('PROD_GO') != '1':
        raise SystemExit(f'prod write blocked ({method} {path}): get explicit approval, then set PROD_GO=1')
    h = {'Accept': 'application/json'}
    if auth or (auth is None and method != 'GET'):
        h['Authorization'] = 'Bearer ' + token()
    data = None
    if body is not None:
        data, h['Content-Type'] = json.dumps(body).encode(), 'application/json'
    url = path if path.startswith('http') else BASE + path
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, h, method=method), timeout=timeout) as r:
            code, raw = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read().decode()
    try:
        d = json.loads(raw, strict=False) if raw else None  # bodies carry raw control chars
    except ValueError:
        return code, raw[:2000]
    return code, d if pii else strip_pii(d)


def _selftest():
    assert strip_pii({'a': [{'email': 'x', 'b': 1}], 'phone': 2}) == {'a': [{'b': 1}]}
    print('ok')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a == ['selftest']:
        _selftest(); sys.exit()
    flags = {x for x in a if x in ('--auth', '--pii')}
    out = a[a.index('--out') + 1] if '--out' in a else None
    pos = [x for i, x in enumerate(a) if x not in flags and x != '--out' and (i == 0 or a[i - 1] != '--out')]
    if len(pos) < 2:
        raise SystemExit(__doc__)
    s, d = call(pos[0], pos[1], json.loads(pos[2]) if len(pos) > 2 else None, auth=True if '--auth' in flags else None, pii='--pii' in flags)
    txt = json.dumps(d, ensure_ascii=False, indent=1)
    if out:
        open(out, 'w').write(txt)
        print(f'{ENV} {s} -> {out} ({len(txt)} chars)')
    else:
        print(f'{ENV} {s}')
        print(txt)
    sys.exit(0 if s < 400 else 1)
