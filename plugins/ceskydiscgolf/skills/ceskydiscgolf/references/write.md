# Writes: recipes and gotchas

Every recipe runs inside the change loop in SKILL.md, on one of **your tournaments**. Paths are relative to `/api` and every call needs a login (Bearer token; `idg.py` adds it).

## Tournament
- **Create:** `POST /tournaments/`. **Leave `is_enabled` out of the body.** `is_enabled:false` archives the event immediately, and every later call (leagues-add, PATCH) then 404s. No hidden draft state exists.
- **Attach the main league:** `POST /tournaments/{t}/leagues-add/ {league_id}`. It brings categories and registration phases, but **not** `info_sections`, so copy those yourself.
- **Edit:** `PATCH /tournaments/{t}/` with only the fields you change (`name`, `info_sections`, ...).
- **Cancel:** `POST /tournaments/{t}/cancel/` both cancels and archives the event, after which the public detail returns 404. Only an authenticated read can still see it.
- `copy-content` copies only info, sponsors and identity. No league or tournament copy feature exists.

## Propositions (propozice)
- Current model: `info_sections`, an ordered array of `{order, title, title_en, content_cz, content_en}`. When sections are set, the legacy `info_cz` HTML blob is ignored, so send `"info_cz":"<p></p>"` alongside them.
- `content_*` may only use the editor's vocabulary: `p strong em u h3 ul ol li a blockquote hr table tbody tr td th img`. No h1, h2 or h4, no `div`, `span`, `style` or classes.
- The server re-serializes on save: it adds `target="_blank" rel=...` to links and escapes `&`. Verify by comparing text with tags stripped, not bytes.
- External `<img src="https://...">` tags survive. The editor's own uploads go through `POST /tournaments/images/upload/` and land in `/media/tournaments/info/*.webp`.
- To convert legacy `info_cz`: split on `<h2>` into sections, strip styles, classes, divs and spans, turn `h4` into `<p><strong>`, note boxes into `blockquote`, and wrap stray inline runs (including image-only links) in `<p>`.

## Rounds, layouts, flights
- New rounds default `preferred_first_tee_time` to 09:00. Fix it with `PATCH /tournaments/{t}/admin-rounds/{r}/`.
- Layout per round: `POST /tournaments/{t}/admin-rounds/{r}/division-layouts/ {layout, division_ids:[]}`. An empty list means all categories. On prod, categories created in the new iDG may be rejected with 400 "nemají legacy ID". A single layout with an empty list still scores everyone.
- **Round lock:** once any scorekeeper session has existed for a round, deleting the round or changing its layouts returns 409 "Kolo je uzamčeno". Only renaming still works, and only the ČADG admins can unlock it.
- Cards: `GET .../admin-rounds/{r}/cards/` returns `players[]` with row ids. Then `PATCH .../cards-update/ {"assignments":[{id,starting_hole,tee_time:"09:30",card_order}],"holes_to_skip":"10"}`. A 409 means scorekeepers are already locked on a card. Publishing is a separate call: `POST .../publish-groups/ {"published":true}`, and players see the flights after that. Key players by (name, category), because duplicate names exist.
- The PDGA nightly pull (03:30 UTC) can replace round layouts with "PDGA (externí)" layouts when PDGA category codes match. Never call `pdga/.../push-registrations/`, because PDGA deletes every registrant missing from the payload.

## Registrations and payments
- **Add a player:** `POST /tournaments/{t}/add-player/ {user, division, override:true}`. `override` bypasses a closed registration phase.
- **Edit or remove:** `PATCH` or `DELETE /tournaments/{t}/players/{adminRowId}/`, where the row id comes from `admin-players/`.
- **Payment:** send both fields, because neither drives the other: `{is_paid:true, payment_status:"<method>"}` or `{is_paid:false, payment_status:"unpaid"}`. Many old rows are `is_paid=1` with `payment_status=unpaid`, so treat "unpaid" as `is_paid=false`.
- **Doubles partner:** `POST /tournaments/{t}/players/{founderRowId}/add-partner/` as admin or TD creates the partner as confirmed and sends no e-mail.
- Ask before any write that might e-mail players: registrations, waiting-list moves, publishing. Say so in the plan.

## Leagues
- League rules lock once any league event has a registered player (409 `registration.has_registered_players`). Repointing a league slot recomputes fees.

## Clubs
- `POST /core/clubs/{uuid}/members/add/ {user_id}` and `DELETE /core/clubs/{uuid}/members/{user_id}/` need a club director or editor login. Both are untested, so re-read the member list afterwards.
