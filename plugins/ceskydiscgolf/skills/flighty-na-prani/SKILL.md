---
name: flighty-na-prani
description: Draft the first-round shotgun flights for a tournament from players' flight wishes ("flighty na přání", a Google Form answer sheet) and the IDG registration, then optionally write them to ceskydiscgolf.cz. Use when a tournament director asks to prepare, draft or assign flights/groups (flighty, skupiny) by wishes, e.g. for MVP After Dark Series.
---

# Flighty na přání

Builds on two skills: **google:gsheets** (reads the wishes sheet; the `google` plugin is a dependency) and **ceskydiscgolf** (registration, cards, writes). Follow their rules, especially the ceskydiscgolf change loop and the check that the tournament is one of *your tournaments*.

## Sources

- **Players: always IDG**, never a reglist tab in the sheet (those go stale). The 1st round's `cards/` gives the card row ids and `max_holes`. `admin-players/` gives the IDG rating.
- **Wishes:** form answers with columns `time | tournament | your name | want to play with`. Find the sheet with gsheets `list "<league or series name>"` (e.g. "After Dark"), confirm it with the director, then pick the wishes tab from `tabs`. Players type the tournament as free text ("Kamýk", "Kamyk", "MVP After Dark #1 - KAMÝK"), so filter by the course keyword without diacritics.
- Wishes apply only to round 1. Later rounds are grouped by score, so leave them alone.

## Ask first

Before drafting, ask the director (one AskUserQuestion, both questions):
1. **Which hole their own flight starts on.** Usually hole 1, but not always.
2. **Any instructions beyond the wish list**, e.g. extra pairings, people to keep apart, a player who arrives late, the hole count if the layout isn't final.

Extra pairings: append them to `wishes.tsv` as rows (`<time>\t<keyword>\t<name>\t<name, name>`) and rerun. Anything the script can't express (keep apart, a fixed hole for a flight): move the players in the draft by hand, then edit the payload to match.

## Steps

```bash
IDG=${CLAUDE_PLUGIN_ROOT}/scripts/idg.py
T=<tournament uuid>; R1=<round 1 id from admin-rounds/>
python3 $IDG GET /tournaments/$T/admin-rounds/$R1/cards/ --auth --out /tmp/cards.json
python3 $IDG GET /tournaments/$T/admin-players/ --auth --out /tmp/players.json
# via the google:gsheets skill: sheets.py read <sheet id> "'<wishes tab>'" > /tmp/wishes.tsv
python3 ${CLAUDE_SKILL_DIR}/scripts/flights.py /tmp/cards.json /tmp/players.json /tmp/wishes.tsv <keyword> [--holes N] --director "<name>" --director-hole <H> --out /tmp/payload.json
```

What the script does:
- It joins every wish chain into one flight, so A+B and B+C put A, B and C together.
- It uses as many flights as there are holes (`--holes` overrides the layout count when the layout isn't ready yet), but never more than players ÷ 4.
- It balances the flight sizes.
- It places the wish groups first, then fills the free spots so the levels **mix**: every flight aims at the overall average IDG rating, so the top players end up in different flights. Each flight in the draft shows its average.
- It puts the director's flight on `--director-hole` and the other flights on the remaining holes in order.

`*` marks a player who has a wish.

Show the user the draft and the lines **"Nenalezeno v registraci"** (a name typo, or a player who isn't registered) and **"Přání větší než flight"**. Fix them by hand before writing anything.

## Writing to IDG (only after an explicit OK)

Use the ceskydiscgolf change loop: back up `cards/`, then `PATCH .../admin-rounds/$R1/cards-update/` with the payload, re-read and diff. Publishing (`publish-groups`) is a separate step, and players see the flights after it. Ask about it separately.

Matching is by full name without diacritics, with the surname as a fallback when it is unique. Nicknames with a shared surname won't match, so they show up under "Nenalezeno".
