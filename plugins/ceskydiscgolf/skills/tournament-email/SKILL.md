---
name: tournament-email
description: Compose the pre-tournament info e-mail ("info před turnajem", "první info", "finální info") for players of a disc golf tournament the user directs. Use when the user asks to write or draft an info e-mail, reminder or announcement for a tournament (e-mail hráčům, mail na turnaj).
---

# Tournament info e-mail

The user is the **director** of the tournament. This skill writes the e-mail; the director sends it themselves, any way they like. Tournament data comes from the `ceskydiscgolf` skill, so run its scripts as it describes. Take the director's first name for the signature from `GET /user/me/ --auth`, or ask. Every fact in the e-mail has a **source**: the propositions, the tournament settings, the director's message, or their answer. A fact with no source stays out.

Optional helper: `humanizer` (`/plugin marketplace add blader/humanizer`, then `/plugin install humanizer@humanizer`). When it is missing, say once that it would help, with its install command, and carry on without it.

## 1. Pin the tournament

List the director's events (`GET /tournaments/managed/ --auth`) and match the name, place or date they gave. Done when exactly one UUID is chosen and its name and date are stated back to them. With several candidates, or none upcoming, ask which one.

## 2. Collect the facts

From `GET /tournaments/{uuid}/`, record:

- `info_sections`: the propositions. They are often league-wide, so the times in them are approximate.
- `rounds[].preferred_first_tee_time`: the exact tee time of each round. The round count comes from this too.
- `registered_count` and `capacity`.
- Links in the raw JSON (`grep -o 'https\?://[^" ]*'`). The flight form lives here and changes each season.

From `GET /tournaments/{uuid}/admin-players/ --auth`, record the status counts.

## 3. Cross-check the catalog

The catalog is what Czech tournament info e-mails contain. It was distilled from about 25 e-mails received and sent in 2026. Go through every item: mark it **covered** (with its source) or **missing**. Done when every item carries one of the two marks, or is skipped because it doesn't fit the event type (an evening glow event has no lunch break).

**Almost always in the e-mail:**

1. **Harmonogram:** registration or package pick-up (where, usually the TC or hole 1), meeting time and place, tee time of each round, lunch break, awards ceremony. It is marked as approximate, with the next tee time confirmed on the spot. The props give only approximate times, so ask for the meeting time and place.
2. **Hřiště / layout:** fixed layout or modified, number of holes, added OB or mandatory, the map or caddy book on the tournament page, and when the details will follow (for example "with the flights").
3. **Flight na přání:** the form link (or "reply to this e-mail") plus the **deadline**. The deadline is usually the director's call, not the props'.
4. **Scoring:** live scoring on ceskydiscgolf.cz (or PDGA Live), who writes the scores (at least 2 per group, or everyone), and the **password**.
5. **Odhlášení:** via the button on the tournament page, otherwise by reply to the e-mail.
6. **Parkování:** where to park, where it is **forbidden**, and public transport. The props almost never cover this, so ask.

**Often, depending on the event:**

7. **Startovné:** a reminder to pay by QR before the event. Leave it out when tagovačka sends the payment reminders (MVP After Dark, for example).
8. **Jídlo a občerstvení:** length of the lunch break, "bring food with you", coffee or tea in the TC, lunch pre-order.
9. **Počasí a stav hřiště:** snow, mud, mowed or long grass, and the spotting that follows from it.
10. **Disc orders delivered to the event:** Ultimo or letitfly, with the order deadline.
11. **Vložené soutěže a ceny:** CTP or longest putt (on which hole), acepool, lottery, "don't run off after the awards".
12. **Pravidla a bezpečnost:** PDGA or ČADG rules, no alcohol during rounds, shouting "Fore" and spotting.
13. **Disc rules for glow events:** only glow discs, or discs with glow stickers or lights.
14. **Kategorie and waiting list:** "check your division" (rating), and a waiting list **only when** `admin-players` has a `waiting_list` row.
15. **What comes next:** "flighty pošlu v sobotu večer", "details with the flights".
16. **Kontakt:** reply to this e-mail, or a phone number.

## 4. Ask what to add

Show the director a short list:
- the missing items from the first group (1–6),
- the items from the second group that suit this event,
- the facts you found in the props that will go in.

Ask what they want to add or change. Always ask when their request gave no extra information. Skip this only when their request already covers every missing item. Done when every item is filled in or they drop it.

## 5. Compose

Write in Czech, in the director's voice:
- Open with "Ahoj všem," (on the evening before, "Pěkný večer všem,").
- Close with "Ať to lítá!", "Na viděnou na <místo>, ať to lítá!" or "Vidíme se zítra,", then sign with the director's first name.

Keep it short and informative. Use the items that have a source and leave out the rest.

Pick the form by event:
- **A short evening or glow event:** an intro of 1–2 sentences, a paragraph with the sraz, start, rounds and layout, then "Pár věcí na připomenutí:" with a short list, then the odhlášení paragraph. See [example.html](example.html), the approved form.
- **A full-day event:** a short bold heading per topic (Harmonogram, Parkování, Hřiště), then "A zbytek stručně:" with a list.

Use HTML: bold only for key facts (times, places, deadlines, hole count) and the short headings, link text instead of bare URLs, and plain paragraphs and lists for the rest.

If the `humanizer` skill is installed, run it on the draft as the last check, then reread the result against the facts you collected: it must keep the Czech, the facts and the names unchanged, so undo any edit that adds, drops or rewords a fact.

## 6. Review

Write the e-mail to `<tournament-slug>-info.html` in the working directory, and show the subject and the plain text in the chat. The director can open the HTML file in a browser and copy it into their mail client with the formatting intact. Iterate on their feedback, rewriting the same file. Done when they approve the text.

## 7. Hand over

Give the director the final subject and the file path. Remind them to send it with the players in **BCC**.

When they ask for the recipients, take the `admin-players` rows with `status == "registered"`. Use `email`, falling back to `user_email`, lowercased and deduplicated. Write them comma-separated to a file and report the count and any rows without an e-mail. Keep the addresses out of the chat.
