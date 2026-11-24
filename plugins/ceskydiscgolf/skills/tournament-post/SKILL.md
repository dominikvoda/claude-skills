---
name: tournament-post
description: "Write the post-tournament report for social media (Facebook page of a league or club) from ceskydiscgolf.cz results, the page's past posts and the event photos, then schedule it for the director's approval. Use when a tournament director asks for a report, recap or post about a finished event (report z turnaje, post na FB, příspěvek na socky)."
---

# Report z turnaje na sociální sítě

Builds on **ceskydiscgolf** (client, *your tournaments* check), the **facebook** plugin (past posts of the page, scheduling) and **google:gdrive** (photos). Follow their rules. Works for any league or club page: everything series-specific comes from the event's own data, propositions and page. Without the `facebook` plugin, ask the director to paste a few past reports as the style reference, and hand over the text and the album list for posting by hand.

## Voice

The post is the director talking to the players. A reader must not be able to tell it was generated.

- Write short, concrete, colloquial Czech in the style of the page's own reports. Every sentence tells a player something they care about.
- Keep one or two numbers that surprise (the hardest hole, an ace, the best round of the night). Numbers that follow from the format (capacity = holes × 5 on a shotgun), averages of easy holes and anything that reads like a table stay out.
- Describe conditions as the players lived them, in the director's words. Neither photos nor weather data say how the night felt or how it compared with the forecast.
- Mark `po rozhozu` on the podium player who won the throw-off (`tiebreak` in the facts), as the page's past posts do.

## Every claim has a source

Allowed sources: IDG data (`post_facts.py`), the tournament's and league's propositions (`info_sections`), the director's answers, and the page's past posts. A claim without one stays out of the post.

- Rules and their consequences (what happens to an unclaimed Ace pool, prizes, league scoring) come from the propositions: `GET /tournaments/{uuid}/` and `GET /leagues/leagues/{leagueId}/`, field `info_sections`. When they don't say, ask.
- Weather data (Open-Meteo, ČHMÚ) only checks what the director says. It is a model or a station a few km away, and its cloud cover can contradict the photos.
- Hole numbers: event layouts with temporary holes renumber the fixed ones. Map them with the director's info e-mail or the layout before naming a hole.

## Steps

Paths are relative to this skill's directory.

1. **Facts.** `python3 -I scripts/post_facts.py <uuid> --out /tmp/post_facts.json`: podiums with to par and `tiebreak`, finishers, best rounds, aces (scores of 1 on the cards), hole averages and the next two events of the same main league. It stops when `results/` is empty, which means the event isn't closed yet (`ceskydiscgolf` references/close.md). Then read the propositions for the rules the post touches.
2. **Style.** Find the page with `facebook` `fb.py pages`, then `fb.py posts <page> 40 --out /tmp/page_posts.json`. Read the 3–5 latest reports of the same series (long text with an album) and reuse their structure: intro, thanks, podium per category with 🥇🥈🥉 and to par, a fact or two, the next event with its link.
3. **Ask the director**, in one message: how the night went for the players (conditions, anything that happened), whom to thank, which page, the publish time, and the Drive folder with photos.
4. **Photos.** `gdrive.py ls <folder>`, then `get` into a new, empty folder. View copies shrunk with `sips -s format jpeg -Z 900`. Build the album:
   - **cover: the photo of everyone together** (group photo),
   - then atmosphere shots, then the podiums in the order of the categories in the text,
   - one version of each shot (pick portrait or landscape, not both),
   - captions state only what the photo shows (`Pódium MPO`). Tell the podiums apart by facts (category, birth years from `admin-players/` when you direct the event), or ask. Never name individual people in a photo.
5. **Draft.** Show the text and the album list. List every claim you are unsure of. Proofread the Czech, including the director's own changes, and point out typos rather than fixing them silently. Done when the director approves the text and the time.
6. **Schedule.** Convert to JPEG: `sips -s format jpeg -s formatOptions 90 -Z 2048 <heic> --out <dir>/<name>.jpg`. Write `album.json` (`[{"file", "caption"}]`), then `FB_GO=1 fb.py schedule <page> <text file> --at <ISO time> --album album.json`. Read the post back (`message`, `attachments`, `scheduled_publish_time`). The director can still edit it in Meta Business Suite → Plánovač (`https://business.facebook.com/latest/content_calendar?asset_id=<page id>`).
   - Add a photo to a scheduled post: upload it with `published=false, temporary=true`, then `POST /{post id}` with the full `attached_media[i]` list in the new order. The message stays as it is.
7. **Learn.** If the director edits the post in Plánovač, read it back, diff it against your draft and ask about each change. Propose a rule for this skill when the reason generalizes.
