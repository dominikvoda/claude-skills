#!/usr/bin/env python3
"""Facebook Pages via the Meta Graph API. Python 3.9+, stdlib only.

  fb.py connect                       log in to Facebook in the browser -> page tokens in pages.json
  fb.py setup                         fallback: token.txt (user token) -> page tokens in pages.json, then empties token.txt
  fb.py pages                         pages you can use
  fb.py posts <page> [n] [--out F]    the page's own posts, newest first (default 25)
  fb.py schedule <page> <text file> --at <ISO time | unix> [--link URL] [--album album.json]   needs FB_GO=1
      album.json: [{"file": "a.jpg", "caption": "..."}, ...]  JPEG/PNG only (convert HEIC first)
  fb.py delete <page> <post id>       needs FB_GO=1

Files in ~/.config/claude-facebook/ (FB_DATA overrides), all private:
  token.txt  setup only: a user access token from Graph API Explorer, pasted by the user
  pages.json written by connect / setup; never print it
connect gets a long-lived token from the Tagovačka token broker (FB_BROKER overrides its origin),
which holds the Meta app secret; RFC 8252 loopback redirect + PKCE.
<page> is a page id or a case-insensitive part of its name.
"""
import base64, hashlib, http.server, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request, webbrowser

GRAPH = 'https://graph.facebook.com/v27.0'
DATA = os.path.expanduser(os.environ.get('FB_DATA', '~/.config/claude-facebook'))
TOKEN, PAGES = (os.path.join(DATA, f) for f in ('token.txt', 'pages.json'))
BROKER = os.environ.get('FB_BROKER', 'https://api-discgolf-tags.dominikvoda.com').rstrip('/')


def private(path, initial):
    """Create the file 600 if missing, keep it 600 (POSIX modes; Windows has none)."""
    os.makedirs(DATA, mode=0o700, exist_ok=True)
    if not os.path.exists(path):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, initial.encode())
        os.close(fd)
    elif os.name == 'posix' and os.stat(path).st_mode & 0o077:
        os.chmod(path, 0o600)


def graph(method, path, **params):
    data = None
    url = GRAPH + path
    if method in ('GET', 'DELETE'):
        url += '?' + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data, method=method), timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read() or b'{}').get('error', {})
        raise SystemExit(f"{method} {path} -> {e.code}: {err.get('message')} (code {err.get('code')})")


def upload(path, file, **params):
    """multipart POST of one image file as `source`."""
    b = '----fb' + os.urandom(8).hex()
    body = b''.join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in params.items())
    ctype = 'image/png' if file.lower().endswith('.png') else 'image/jpeg'
    body += (f'--{b}\r\nContent-Disposition: form-data; name="source"; filename="{os.path.basename(file)}"\r\n'
             f'Content-Type: {ctype}\r\n\r\n').encode() + open(file, 'rb').read() + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request(GRAPH + path, body, {'Content-Type': f'multipart/form-data; boundary={b}'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read() or b'{}').get('error', {})
        raise SystemExit(f"POST {path} ({file}) -> {e.code}: {err.get('message')} (code {err.get('code')})")


def save_pages(tok):
    """User token -> a token per page in pages.json, then print each page's expiry."""
    pages = graph('GET', '/me/accounts', access_token=tok, fields='id,name,access_token,tasks', limit=100)['data']
    if not pages:
        raise SystemExit('The token sees no pages: grant pages_show_list and pick your pages in the Facebook login dialog.')
    private(PAGES, '{}')
    json.dump({p['id']: {'name': p['name'], 'access_token': p['access_token'], 'tasks': p.get('tasks', [])} for p in pages},
              open(PAGES, 'w'))
    for p in pages:
        # expires_at 0 = never; a page token from a short-lived user token dies with it (~1-2 h)
        try:
            info = graph('GET', '/debug_token', input_token=p['access_token'], access_token=p['access_token'])['data']
        except SystemExit as e:
            print(f"{p['name']} ({p['id']}): saved, expiry unknown ({e})")
            continue
        exp = info.get('expires_at', 0)
        print(f"{p['name']} ({p['id']}): expires {'never' if not exp else time.strftime('%Y-%m-%d %H:%M', time.localtime(exp))}, "
              f"scopes {','.join(info.get('scopes', []))}")


def setup():
    private(TOKEN, '')
    tok = open(TOKEN).read().strip()
    if not tok:
        raise SystemExit(f'Paste a user access token from Graph API Explorer into {TOKEN} with a text editor (not in the chat), then rerun. '
                         'Prefer fb.py connect, which needs no pasting.')
    save_pages(tok)
    open(TOKEN, 'w').close()


def connect():
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state, got = secrets.token_urlsafe(16), {}

    class Callback(http.server.BaseHTTPRequestHandler):
        timeout = 5  # browsers open idle pre-connects; without this one blocks the single-threaded server

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            # Only an answer carrying our state ends the wait, so a stray or hostile request cannot cancel the login.
            if u.path != '/cb' or not secrets.compare_digest(q.get('state', ''), state):
                self.send_error(400)
                return
            got.update(q)
            ok = 'code' in got
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            msg = 'Hotovo, můžeš zavřít okno.' if ok else 'Propojení se nepovedlo, podívej se do terminálu.'
            self.wfile.write(f'<!doctype html><meta charset="utf-8"><title>Facebook</title><p>{msg}</p>'.encode())

        def log_message(self, *args):
            pass

    srv = http.server.HTTPServer(('127.0.0.1', 0), Callback)
    redirect = f'http://127.0.0.1:{srv.server_port}/cb'
    url = BROKER + '/api/facebook/authorize?' + urllib.parse.urlencode(
        {'redirect_uri': redirect, 'code_challenge': challenge, 'code_challenge_method': 'S256', 'state': state})
    print(f'Opening Facebook login in the browser. If nothing opens, visit:\n{url}')
    webbrowser.open(url)
    deadline = time.time() + 300
    while not got and time.time() < deadline:
        srv.timeout = deadline - time.time()
        srv.handle_request()
    srv.server_close()
    if not got:
        raise SystemExit('No answer from the browser within 5 minutes: run fb.py connect again.')
    if 'code' not in got:
        raise SystemExit(f"Facebook connect failed: {got.get('error', 'no code')}. Run fb.py connect again.")
    # Own User-Agent: Cloudflare in front of the broker refuses Python-urllib's (403, error code 1010).
    req = urllib.request.Request(BROKER + '/api/facebook/token',
                                 json.dumps({'code': got['code'], 'code_verifier': verifier, 'redirect_uri': redirect}).encode(),
                                 {'Content-Type': 'application/json', 'User-Agent': 'claude-skills-facebook'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            tok = json.loads(r.read())['access_token']
    except urllib.error.HTTPError as e:
        raise SystemExit(f'POST {BROKER}/api/facebook/token -> {e.code}: run fb.py connect again.')
    except (urllib.error.URLError, ValueError, KeyError) as e:
        raise SystemExit(f'POST {BROKER}/api/facebook/token failed ({type(e).__name__}): run fb.py connect again.')
    save_pages(tok)


def page(key):
    if not os.path.exists(PAGES):
        raise SystemExit('No pages yet: run fb.py connect.')
    pages = json.load(open(PAGES))
    hits = [i for i, p in pages.items() if key == i or key.lower() in p['name'].lower()]
    if len(hits) != 1:
        raise SystemExit(f"'{key}' matches {[pages[i]['name'] for i in hits] or 'no page'}; known: {[p['name'] for p in pages.values()]}")
    return hits[0], pages[hits[0]]['access_token']


def main(a):
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    cmd = a[0] if a else ''
    if cmd == 'connect':
        connect()
    elif cmd == 'setup':
        setup()
    elif cmd == 'pages':
        private(PAGES, '{}')
        for i, p in json.load(open(PAGES)).items():
            print(i, p['name'], ','.join(p['tasks']))
    elif cmd == 'posts' and len(a) >= 2:
        pid, tok = page(a[1])
        n = int(a[2]) if len(a) > 2 and a[2].isdigit() else 25
        posts, path, params = [], f'/{pid}/posts', {'access_token': tok, 'limit': min(n, 100),
                                                  'fields': 'created_time,message,message_tags,permalink_url,full_picture,attachments{media_type,url}'}
        while len(posts) < n:
            r = graph('GET', path, **params)
            posts += r.get('data', [])
            after = r.get('paging', {}).get('cursors', {}).get('after')
            if not after or not r.get('paging', {}).get('next'):
                break
            params['after'] = after
        s = json.dumps(posts[:n], ensure_ascii=False, indent=1)
        open(opt('--out'), 'w').write(s) if opt('--out') else print(s)
    elif cmd == 'schedule' and len(a) >= 3 and opt('--at'):
        if os.environ.get('FB_GO') != '1':
            raise SystemExit('Page write blocked: show the post and the time, get an explicit OK, then rerun with FB_GO=1.')
        pid, tok = page(a[1])
        params = {'access_token': tok, 'message': open(a[2]).read().strip(), 'published': 'false',
                  'scheduled_publish_time': opt('--at')}
        if opt('--link'):
            params['link'] = opt('--link')
        if opt('--album'):
            album = json.load(open(opt('--album')))
            bad = [x['file'] for x in album if not x['file'].lower().endswith(('.jpg', '.jpeg', '.png'))]
            if bad:
                raise SystemExit(f'JPEG/PNG only, convert first: {bad}')
            for i, x in enumerate(album):
                # temporary=true: an unpublished photo that a scheduled post can attach
                ph = upload(f'/{pid}/photos', x['file'], access_token=tok, published='false', temporary='true',
                            caption=x.get('caption', ''))
                params[f'attached_media[{i}]'] = json.dumps({'media_fbid': ph['id']})
                print('uploaded', x['file'], ph['id'])
        post = graph('POST', f'/{pid}/feed', **params)['id']
        got = graph('GET', f'/{post}', access_token=tok, fields='scheduled_publish_time,is_published')
        print(post, 'is_published', got.get('is_published'), 'scheduled_publish_time', got.get('scheduled_publish_time'))
    elif cmd == 'delete' and len(a) >= 3:
        if os.environ.get('FB_GO') != '1':
            raise SystemExit('Page write blocked: get an explicit OK, then rerun with FB_GO=1.')
        pid, tok = page(a[1])
        print(graph('DELETE', f'/{a[2]}', access_token=tok))
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
