# Closing a tournament (uzavření)

Runs inside the change loop in SKILL.md, on one of **your tournaments**.

`POST /tournaments/{uuid}/close/` writes places from the scores and league points, then locks the scores. Players on a shared score keep a shared place. A podium tie gets its real order (rozhoz, play-off) only through `POST .../finalize-places/` afterwards, and that call changes places only: the points stay as closing wrote them.

## Steps

1. **Read.** Run `python3 -I scripts/close_check.py <uuid>`. It prints the name, director, `is_closed`, the top 5 per category from the live leaderboard, every `UNFINISHED` player and every `PODIUM TIE` (a shared place touching 1st–3rd), and saves the leaderboard to `/tmp/close_check_leaderboard.json`. Done when every registered player is on the leaderboard and each `UNFINISHED` player is either scored or confirmed DNF by the director.
2. **Podium ties.** No `PODIUM TIE` line: go to step 3. Otherwise list the tied groups to the director and ask (one AskUserQuestion) how each one really ended, with two options:
   - **They say the order.** Write `/tmp/places.json` as `{"places":[{"tournament_player_id","place"}]}` from the saved leaderboard, keyed by `user_id` (names repeat).
   - **Pull it from Tagovačka** (the `tagovacka` skill): `python3 -I ../tagovacka/scripts/tag.py idg <uuid> <start date> --out /tmp/tag_mgmt.json`, then `python3 -I scripts/close_check.py <uuid> --tagovacka /tmp/tag_mgmt.json --out /tmp/places.json`. It builds the payload from Tagovačka's manual/official places and prints every group Tagovačka has `NOT DECIDED`; ask the director about those.
   Done when every member of every podium tie group has a distinct place, confirmed by the director.
3. **Plan.** Back up `close-status/`, `results/` and the leaderboard under `~/idg-backup/<env>/`. Show the event, the director, the final podium per category, `waitlist_cancelled` risk, and the calls below, then wait for an explicit go.
4. **Run**, each with `PROD_GO=1`:
   - `POST /tournaments/{uuid}/close/ {}` → `places_written`, `leagues_processed`, `waitlist_cancelled`, `pdga_pull_queued`.
   - Only with ties: `POST /tournaments/{uuid}/finalize-places/` with `/tmp/places.json` → `updated` equals the payload length.
5. **Verify.** `GET .../close-status/ --auth` shows `is_closed: true`, and the podium in `GET .../results/ --auth` matches the one from step 3.

## Gotchas

- `results/` stays empty (`divisions: []`) until the event is closed; before that the live leaderboard is the only standings source.
- `close/` returns 409 `results_incomplete` with `players[]` when a registered player has an unscored round and isn't DNF.
- `close/` cancels everyone still on the waiting list (`waitlist_cancelled`).
- PDGA events queue a background pull of PDGA scores and ratings (`pdga_pull_queued`). IDG event ratings arrive about a day later from a job; no API triggers them.
- Undo: `POST .../finalize-places/reset/ {}` clears the manual places; `POST .../reopen/ {}` reopens the event.
- Whether closing e-mails players is untested.
