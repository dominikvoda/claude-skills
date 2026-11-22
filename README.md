# claude-skills

Claude Code plugins by [Dominik Voda](https://github.com/dominikvoda).

| Plugin | Skills | What it does |
|---|---|---|
| `ceskydiscgolf` | `ceskydiscgolf`, `flighty-na-prani`, `tournament-email` | Work with [ceskydiscgolf.cz](https://ceskydiscgolf.cz) (iDiscGolf): look up tournaments, players and results, manage the tournaments you direct, draft flights from players' wishes, write the pre-tournament info e-mail. |
| `google` | `gsheets`, `gmail` | Read Google Sheets you have access to; read and send Gmail (every send needs your explicit OK). |

## Install

```
/plugin marketplace add dominikvoda/claude-skills
/plugin install ceskydiscgolf@claude-skills     # also installs google (dependency)
/plugin install google@claude-skills            # Google only
```

Updates are not automatic for third-party marketplaces: run `/plugin marketplace update claude-skills`, or turn on auto-update in `/plugin` → Marketplaces.

Requirements: Python 3.9+, and [uv](https://docs.astral.sh/uv/) for the Google scripts.

## Setup

Credentials stay on your machine, outside this repo and outside the plugin folder:

| What | Where |
|---|---|
| ceskydiscgolf.cz login | `~/.ceskydiscgolf.json`, mode 600: `{"username": "...", "password": "..."}` |
| Google OAuth client + tokens | `~/.config/claude-google/` (`credentials.json`, `sheets-token.json`, `gmail-token.json`) |

Create the IDG file yourself in an editor, never by pasting the password into Claude:

```bash
install -m 600 /dev/null ~/.ceskydiscgolf.json
```

For Google, every user brings their own OAuth client (a Desktop app in their own Google Cloud project). Step-by-step instructions are in the Setup section of [`gsheets`](plugins/google/skills/gsheets/SKILL.md).

## Pro ředitele turnajů (česky)

1. V Claude Code: `/plugin marketplace add dominikvoda/claude-skills` a `/plugin install ceskydiscgolf@claude-skills`.
2. Založ `~/.ceskydiscgolf.json` se svým přihlášením na ceskydiscgolf.cz (viz výše, `chmod 600`).
3. Pro flighty na přání z Google formuláře nastav Google přístup podle návodu ve skillu [`gsheets`](plugins/google/skills/gsheets/SKILL.md).
4. Pak stačí psát normálně: „najdi můj turnaj na Kamýku“, „poskládej flighty na přání“, „napiš info e-mail hráčům“.

Claude nic nezapíše do ceskydiscgolf.cz ani neodešle e-mail, dokud mu to výslovně neodsouhlasíš.

## License

MIT
