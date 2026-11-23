---
name: tagovacka
description: "Read Tagovačka (tagovacka.cz), the club tag and tournament app that mirrors ceskydiscgolf.cz events: standings, podium tie-breaks (rozhozy) and tournaments you manage there. Use when the user mentions Tagovačka or wants the tie-break results stored in it. Triggers: tagovačka, tagovacka, rozhozy, rozhoz."
---

# Tagovačka (read-only)

Tagovačka syncs ceskydiscgolf.cz events and adds what IDG lacks, mainly the director's **manual tie-breaks** (rozhozy) for podium ties. Closing an event on ceskydiscgolf.cz can take its tie-breaks from here (`ceskydiscgolf` references/close.md).

| | |
|---|---|
| Website | `https://tagovacka.cz` |
| API | `https://api-discgolf-tags.dominikvoda.com/api` |

## Login

The user's own Tagovačka account (e-mail + password), stored in `~/.tagovacka.json` as `{"email": "...", "password": "..."}` (`TAG_CREDS` points elsewhere). On the first call `tag.py` creates the file empty and private. Tell the user the path and ask them to fill it in with a text editor (or open it for them: `open -a TextEdit ~/.tagovacka.json` on macOS). The password must never pass through the chat, and the token stays in memory.

A 403 "Error 1010" is Cloudflare rejecting the client's User-Agent; `tag.py` sends a browser one, so use `tag.py` rather than raw `curl`/urllib.

## Tools

Paths are relative to this skill's directory.

```bash
python3 -I scripts/tag.py idg <IDG tournament uuid> <YYYY-MM-DD> --out /tmp/tag_mgmt.json   # find the event, dump its management view
python3 -I scripts/tag.py GET /tournaments/<tagovacka id>/management [--out FILE]
```

`idg` searches the events you manage on that day and matches `idgV2Uuid`, so it needs the event's start date from `GET /tournaments/{uuid}/` on ceskydiscgolf.cz.

## Reads

- `GET /manageable-tournaments?from=YYYY-MM-DD&to=YYYY-MM-DD`: events you direct or hold a manager grant on (a system admin sees all). Rows: `id` (Tagovačka int id), `name`, `dateStart`, `resultsFinalizedAt`. No IDG UUID here.
- `GET /tournaments/{id}/management`: `idgV2Uuid`, `name`, and `standings`:
  - `standings.resultsComplete`: every player has every round.
  - `standings.divisions[]`: `division` (IDG abbreviation, e.g. `MPO`), `finishers[]`, `podiumTieGroups[]`.
  - finisher: `position` (effective: official → manual → score rank), `derivedPosition` (score rank), `isTied`, `isManual` (director's tie-break), `isOfficial` (taken from the source), `idgV2UserId` (= IDG `user_id`; the founder for doubles), `playerName`, `totalScore`.
  - tie group: `basePosition`, `positions`, `resolved`, `officiallyResolved`.

Writes (setting tie-breaks) happen in the Tagovačka web UI, not through this skill.
