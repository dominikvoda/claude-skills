#!/usr/bin/env python3
"""Facebook Pages via the Meta Graph API. Python 3.9+, stdlib only.

  fb.py setup                         token.txt (user token) -> page tokens in pages.json, then empties token.txt
  fb.py pages                         pages you can use
  fb.py posts <page> [n] [--out F]    the page's own posts, newest first (default 25)
  fb.py schedule <page> <text file> --at <ISO time | unix> [--link URL] [--album album.json]   needs FB_GO=1
      album.json: [{"file": "a.jpg", "caption": "..."}, ...]  JPEG/PNG only (convert HEIC first)
  fb.py delete <page> <post id>       needs FB_GO=1

Files in ~/.config/claude-facebook/ (FB_DATA overrides), all private:
  app.json   {"app_id": "...", "app_secret": ""}   secret optional: with it, setup exchanges a short token itself
  token.txt  a user access token from Graph API Explorer, pasted by the user
  pages.json written by setup; never print it
<page> is a page id or a case-insensitive part of its name.
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

GRAPH = 'https://graph.facebook.com/v27.0'
DATA = os.path.expanduser(os.environ.get('FB_DATA', '~/.config/claude-facebook'))
APP, TOKEN, PAGES = (os.path.join(DATA, f) for f in ('app.json', 'token.txt', 'pages.json'))


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


def setup():
    private(APP, '{"app_id": "", "app_secret": ""}\n')
    private(TOKEN, '')
    tok = open(TOKEN).read().strip()
    if not tok:
        raise SystemExit(f'Paste a user access token from Graph API Explorer into {TOKEN} with a text editor (not in the chat), then rerun.')
    app = json.load(open(APP))
    if app.get('app_id') and app.get('app_secret'):
        tok = graph('GET', '/oauth/access_token', grant_type='fb_exchange_token', client_id=app['app_id'],
                    client_secret=app['app_secret'], fb_exchange_token=tok)['access_token']
    pages = graph('GET', '/me/accounts', access_token=tok, fields='id,name,access_token,tasks', limit=100)['data']
    if not pages:
        raise SystemExit('The token sees no pages: in Explorer, grant pages_show_list and pick your pages in the login dialog.')
    private(PAGES, '{}')
    json.dump({p['id']: {'name': p['name'], 'access_token': p['access_token'], 'tasks': p.get('tasks', [])} for p in pages},
              open(PAGES, 'w'))
    open(TOKEN, 'w').close()
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


def page(key):
    if not os.path.exists(PAGES):
        raise SystemExit('No pages yet: run fb.py setup.')
    pages = json.load(open(PAGES))
    hits = [i for i, p in pages.items() if key == i or key.lower() in p['name'].lower()]
    if len(hits) != 1:
        raise SystemExit(f"'{key}' matches {[pages[i]['name'] for i in hits] or 'no page'}; known: {[p['name'] for p in pages.values()]}")
    return hits[0], pages[hits[0]]['access_token']


def main(a):
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    cmd = a[0] if a else ''
    if cmd == 'setup':
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
