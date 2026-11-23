# Reads: endpoint map

Paths are relative to `/api`. Public means no login needed. Endpoints marked *your tournaments* need a login and are meant for tournaments you manage.

## Id model
- Tournaments, leagues, clubs, courses, divisions, rounds and layouts are keyed by **UUID**.
- Users have an int `id` (the v2 user id; yours is in `GET /user/me/`). `old_id` ("Staré ID (ČADG)") is the pre-2026 iDiscGolf id and appears only on `/user/users/{id}/`. The two id spaces don't overlap. To match people across systems, use `old_id`, the PDGA number, or the name.
- A registration (`tournament-players` row) has its own UUID. Admin endpoints use the **admin-players row `id`**, not the user id.
- Courses are called **fields** (`/core/fields/`). No `course` path exists.
- Public profile URL: `https://ceskydiscgolf.cz/idg/hraci/{userId}`.

## Tournaments
- `GET /tournaments/`: list. Filters: `?upcoming=true` (future only), `?year=YYYY`. Rows carry `course_name` (a string, not the field UUID), `main_league_name`, `registration_phase_state`, `capacity`, `registered_count`, `pdga_tier`, `division_cadg`. Don't combine `include_external=true` with `upcoming`, because external rows ignore the date filter. `tournament_format` is always null in the list.
- `GET /tournaments/{uuid}/`: detail. Carries `course`, `divisions[]` (with the `division` UUID and `active_player_count`), `rounds[]` (with `id` = round UUID), `leagues[]`, `director1/2`, `info_sections`, `tournament_format` (1 = doubles; 0 or null = singles, and null is common for both). It has no league name, so use the list's `main_league_name`. It returns 404 anonymously when the event is cancelled or archived (`is_enabled=false`). With `--auth` it returns 200 with `is_cancelled`/`cancelled_reason`.
- `GET /tournaments/managed/` and `/my-tournaments/` (auth) list the events you manage.
- `GET /tournaments/{uuid}/editors/` (auth): managers `[{id,user_id,user_name,username}]`.

## Players, results, scores
- `GET /tournament-players/?tournament={uuid}`: roster with `status` (`registered`, `waiting_list`; doubles add `pending_partner`, `cancelled`, `payment_expired`), `is_wild_card`, `division_abbreviation`, ratings. `?user={id}` gives one player's registrations, each with `registration_time`, which is the best signal that an account is actually used.
- `GET /tournaments/{uuid}/admin-players/` (*your tournaments*): admin rows with `id`, `variable_symbol`, `division_price`, `is_paid`, `payment_status`, plus each entrant's e-mail and phone. This is the only place an entrant's e-mail is available; `idg.py` strips it unless you pass `--pii`.
- `GET /tournaments/{uuid}/results/`: final results per division. Rows: `place`, `user_id`, `round_scores` `{"1":53,...}`, `total`, `is_dnf`.
- `GET /scoring/tournaments/{uuid}/live-scoring/leaderboard/?division={divisionUuid}[&round={roundUuid}]`: live standings with `place` (ties shared), `total`, `thru`, `tournament_player_id`, `user_id` and per-round `hole_scores` `{"1":{hole:score}}`. `division` is required, otherwise the response is empty; without `round` it covers the whole event.
- `GET /scoring/tournaments/{uuid}/live-scoring/rounds/{roundUuid}/holes/?division={divisionUuid}`: the holes and pars a division plays in a round, which tells you its layout.
- `GET /tournaments/{uuid}/admin-rounds/` and `.../admin-rounds/{r}/cards/` (*your tournaments*): round config, layouts, flights.
- Doubles: one entry per team. `user` is the founder, `team_display_name` is the team name, and `members[]` lists `{user_id, role founder|partner, confirmation_status}`. Ratings on roster rows are today's, not the event day's. Use `/ratings/users/{id}/rating-history/` for those.

## People, clubs, courses, categories
- `GET /user/users/?search=` and `/user/users/{id}/`: public, never with e-mail. Fields: `clubs[]`, `membership_type`, `membership_end_date`, `paid_membership_years`, `birth_year`, `old_id`.
- `GET /user/me/` (auth): your own account.
- `GET /ratings/users/{id}/rating-history/` and `/round-ratings/`: public.
- `GET /core/clubs/` (about 119 clubs), `/core/clubs/{uuid}/members/` (with `is_active_cadg_member`), `/core/clubs/{uuid}/editors/`. All public.
- Known club UUIDs: DGC Praha `b4c13a5e-5637-4fdd-a197-35a806dfe4cb`, DGC Ostrava `af3f3af0-6085-4387-9b32-86b748e9dcff`, DGK Horníci Kladno `f8b07131-f074-460f-8c5a-6ab3f7ba9d85`, DGT Prague Hawks `8372baef-71ba-4fe9-929e-4cdbb324cb48`. Resolve others by exact name, never fuzzy, because club names differ by one letter in the wild.
- `GET /core/fields/{fieldUuid}/`: a course with every layout it ever had, including holes. `.../tournament-layouts/` lists tournaments by course, but it is heavy, includes test events, and misses upcoming events with no layouts yet.
- `GET /core/divisions/`: categories (canonical and owner-less ones only). `?for_tournament=` and `?for_league=` add that owner's custom categories.
- Leagues: standings, `point_system` and registration phases live at the league level. A tournament's own `registration-phases/` is empty when the phases come from its league.

## Bulk lookups
Loop in Python with `from idg import call` (see Tools in SKILL.md). Keep it to a few threads so the server isn't hammered. Cache the raw JSON in `/tmp` and analyse that copy instead of re-fetching.
