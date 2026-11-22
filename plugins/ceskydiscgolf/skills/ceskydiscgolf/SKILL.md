---
name: ceskydiscgolf
description: "ceskydiscgolf.cz (new iDiscGolf, \"IDG v2\"), the Czech disc golf association portal. Use to look up tournaments, players, registrations, results, ratings, leagues, clubs or courses (fields) through its REST API, and to manage a tournament you direct: propositions, rounds, layouts, flights, registrations and payments. Triggers: ceskydiscgolf, iDiscGolf, IDG, propozice, flighty."
---

# ceskydiscgolf.cz

Django REST Framework backend + Nuxt frontend.

| | |
|---|---|
| API | `https://api.ceskydiscgolf.cz/api` |
| Website | `https://ceskydiscgolf.cz` (tournament page: `/idg/turnaje/{uuid}`, player: `/idg/hraci/{userId}`) |

The OpenAPI spec is public: `GET /api/schema/?format=json` (about 280 paths, cache it in `/tmp`). Its **request** schemas for tournament sub-endpoints are often copy-pasted and wrong. When a write body is unclear, grep the Nuxt chunks (`https://ceskydiscgolf.cz/_nuxt/*.js`) for the path instead.

## Login

Public reads need no account. Logged-in reads and writes use the user's own ceskydiscgolf.cz account, stored in `~/.ceskydiscgolf.json` as `{"username": "...", "password": "..."}` (`IDG_CREDS` points elsewhere). On the first logged-in call, `idg.py` creates the file empty and private and asks for the login. Tell the user the path and ask them to fill it in with a text editor themselves. The password must never pass through the chat. The client keeps the file private (mode 600) on macOS and Linux.

Keep its contents and every token out of the chat and out of files.

Auth is SimpleJWT: `POST /api/user/token/` returns an access token that lasts 30 min, and `idg.py` mints a fresh one per process. Failed logins are throttled (5/min), so stop after a 401 on login and don't retry.

## Tools

Paths in this skill are relative to its directory (the folder with this SKILL.md).

`python3 scripts/idg.py METHOD PATH [JSON] [--auth] [--pii] [--out FILE]` is the REST client (Python 3.9+, stdlib only). GET runs anonymously unless you pass `--auth`; writes always log in. It strips e-mail and phone fields unless you pass `--pii`. For anything that loops, import it as a library: `sys.path.insert(0, "<this skill dir>/scripts"); from idg import call`.

Remember the trailing slash on every path (without it you get a 301 or 404). Response bodies contain raw control characters, so parse them with `json.loads(..., strict=False)`.

## Your tournaments

Logged-in endpoints that read or change a tournament (`admin-*`, `editors/`, every write) are for **your tournaments**: the UUIDs in `GET /tournaments/managed/ --auth`. Check the target UUID against that list before the first such call, and state its name and date back to the user.

## Reads

See [references/read.md](references/read.md) for the endpoint map, the id model and lookup recipes.

## Writes

Every write follows this **change loop**:

1. **Read** the current state and save it as a backup under `~/idg-backup/<env>/<what>-<ts>.json`, together with the payload that reverts the change.
2. **Show the user the plan**: the exact calls, the affected rows, and what players will see or receive by e-mail. Then wait for an explicit go.
3. **Run** with `PROD_GO=1` set for that one command. The script refuses prod writes without it.
4. **Verify** by re-reading and diffing against the backup. A read right after a write can be stale, so re-read a few minutes later if it looks wrong.

Write recipes and gotchas for tournaments, propositions, rounds, cards, registrations, payments, leagues, clubs and doubles are in [references/write.md](references/write.md).
