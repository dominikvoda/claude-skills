# claude-skills

Pluginy pro [Claude Code](https://code.claude.com/docs/en/overview) pro ředitele disc golfových turnajů na [ceskydiscgolf.cz](https://ceskydiscgolf.cz). Volitelně umí číst i Google tabulky, [Tagovačku](https://tagovacka.cz), pracovat s Gmailem a s facebookovými stránkami. *English summary [at the bottom](#english).*

## Co to umí

Řekneš Claudovi běžnou češtinou, co potřebuješ, a on si data dohledá sám:

- **„Kolik lidí je přihlášených na můj turnaj v Nučicích a kdo ještě nezaplatil?“**: přečte registrace z ceskydiscgolf.cz.
- **„Poskládej flighty na přání na Kamýk.“**: vezme přání hráčů z Google formuláře a registrace z ceskydiscgolf.cz a navrhne skupiny. Splní přání, zbytek hráčů namíchá podle výkonnosti, dá max 5 hráčů na jamku a větší skupiny pošle na jamky, které jsou podle historie turnajů lehčí. Potřebuje [Google přístup](#volitelně-google-tabulky-a-gmail).
- **„Napiš info e-mail hráčům před turnajem.“**: připraví e-mail z propozic a nastavení turnaje a doptá se na to, co v nich chybí (sraz, parkování…).
- **„Uzavři turnaj na Kamýku.“**: zkontroluje, že jsou zapsaná všechna kola, a najde shody na bedně. Když nějaké jsou, zeptá se tě, jak dopadl rozhoz, nebo výsledky vytáhne z Tagovačky. Pak turnaj uzavře a zapíše místa. Rozhozy z Tagovačky potřebují [přihlášení do Tagovačky](#volitelně-tagovačka).
- **„Připrav post na FB z turnaje na Kamýku.“**: z výsledků, propozic a dřívějších postů stránky napíše report ve stylu stránky, z fotek na Google Disku složí album (úvodní je společná fotka) a po tvém schválení post naplánuje. Do zveřejnění ho můžeš upravit v Meta Business Suite. Potřebuje [Facebook](#volitelně-facebook) a [Google přístup](#volitelně-google-tabulky-a-gmail).
- **„Uprav propozice“, „přidej hráče“, „označ platbu“**: správa turnajů, které řídíš.

**Bez tvého souhlasu Claude nic nezmění.** Před každým zápisem na ceskydiscgolf.cz nebo odesláním e-mailu ti ukáže, co přesně udělá, a počká na tvoje „OK“.

| Plugin | Skilly | K čemu |
|---|---|---|
| `ceskydiscgolf` | `ceskydiscgolf`, `flighty-na-prani`, `tournament-email`, `tournament-post`, `tagovacka` | turnaje, hráči, výsledky, propozice, flighty, info e-mail, report z turnaje na FB, uzavření turnaje, čtení Tagovačky |
| `facebook` | `facebook` | volitelné: čtení postů a plánování nových na facebookových stránkách, které spravuješ. Instaluje se zvlášť a funguje až po [nastavení](#volitelně-facebook). |
| `google` | `gsheets`, `gdrive`, `gforms`, `gmail` | volitelné: čtení Google tabulek a Disku (třeba fotek), zakládání a úprava Google formulářů, čtení a odesílání Gmailu. Nainstaluje se samo s `ceskydiscgolf`, ale funguje až po [nastavení](#volitelně-google-tabulky-a-gmail). |

## Průvodce instalací

Zabere asi 5 minut. Po těchhle třech krocích funguje všechno kolem ceskydiscgolf.cz. Google přístup si můžeš [doplnit později](#volitelně-google-tabulky-a-gmail), až ho budeš potřebovat.

### 1. Nainstaluj Claude Code

Claude Code je Claude, který běží v terminálu a umí za tebe spouštět příkazy. Potřebuješ k němu předplatné Claude (Pro nebo Max) nebo účet s API.

Postupuj podle [oficiálního návodu](https://code.claude.com/docs/en/setup). Pak otevři Terminál, napiš `claude` a přihlas se.

Pluginy potřebují ještě **Python 3**. Nemusíš ho řešit předem: když chybí, Claude to pozná a pomůže ti s instalací.

### 2. Přidej pluginy

V Claude Code (po spuštění `claude`) napiš tyhle dva příkazy:

```
/plugin marketplace add dominikvoda/claude-skills
/plugin install ceskydiscgolf@claude-skills
```

Když se zeptá na rozsah (scope), vyber **user**. Pluginy pak budeš mít k dispozici ve všech složkách. Nakonec Claude Code ukonči (`/exit`) a spusť znovu.

✅ **Ověření:** napiš `/plugin` a v seznamu uvidíš `ceskydiscgolf` a `google`.

### 3. Přihlášení na ceskydiscgolf.cz

Claude se na ceskydiscgolf.cz přihlašuje tvým účtem, takže smí totéž, co ty. Turnaje, které řídíš, může spravovat, ostatní jen číst. **Heslo nikdy nepiš do chatu.** Vyplníš ho sám do souboru, který Claude připraví.

1. V Claude Code napiš *„Jaké turnaje na ceskydiscgolf.cz řídím?“*
2. Claude ti napoprvé řekne, že založil soubor `.ceskydiscgolf.json` ve tvé domovské složce, a požádá tě o jeho vyplnění.
3. Otevři ten soubor v textovém editoru (TextEdit, Poznámkový blok…). Doplň do něj svůj login a heslo z ceskydiscgolf.cz, ulož ho a zavři:
   ```json
   {"username": "tvuj-login", "password": "tvoje-heslo"}
   ```
4. Napiš Claudovi, že je hotovo.

✅ **Ověření:** Claude vypíše turnaje, které řídíš.

## Volitelně: Tagovačka

Potřebuješ jen tehdy, když chceš, aby Claude četl data z [Tagovačky](https://tagovacka.cz), třeba výsledky rozhozů při uzavírání turnaje. Funguje to stejně jako u ceskydiscgolf.cz:

1. Napiš Claudovi *„Načti z Tagovačky rozhozy na můj turnaj.“*
2. Claude založí soubor `.tagovacka.json` ve tvé domovské složce (na Macu ti ho rovnou otevře v TextEditu).
3. Doplň svůj e-mail a heslo z Tagovačky, ulož a zavři:
   ```json
   {"email": "tvuj@email.cz", "password": "tvoje-heslo"}
   ```
   Když heslo v TextEditu píšeš ručně, vypni Úpravy → Nahrazování → Chytré uvozovky, jinak se z `"` stanou typografické uvozovky a soubor nepůjde přečíst.
4. Napiš Claudovi, že je hotovo.

Claude z Tagovačky jen čte. Rozhozy zadáváš v Tagovačce sám.

## Volitelně: Google tabulky a Gmail

Tohle nastavení potřebuješ, jen když chceš, aby Claude četl tvoje Google tabulky (třeba odpovědi z formuláře „flight na přání“) nebo pracoval s Gmailem.

Google nedovolí jen tak cizímu programu číst tvoje data. Proto si vytvoříš vlastní malou „aplikaci“, které to povolíš. Uvidí jen to, k čemu máš přístup ty, a nikdo jiný ji používat nebude. Nastavení zabere asi 10 minut a dělá se jednou.

Google skripty potřebují pomocníka [uv](https://docs.astral.sh/uv/). Když ho nemáš, Claude ti ho pomůže nainstalovat.

1. Otevři [Google Cloud Console](https://console.cloud.google.com/), přihlas se svým Google účtem a vytvoř **nový projekt** (jméno je jedno, třeba `claude`).
2. V horním vyhledávání postupně najdi a **zapni** (Enable) **Google Sheets API**, **Google Drive API**, pokud chceš upravovat formuláře, i **Google Forms API**, a pokud chceš e-maily, i **Gmail API**.
3. Otevři **Google Auth Platform** a projdi úvodní nastavení. Vyplníš název aplikace a svůj e-mail, typ uživatelů zvol **External**.
4. V části **Audience** klikni na **Publish app**, aby stav byl **In production**. Bez toho tě Google každých 7 dní odhlásí.
5. V části **Clients** klikni na **Create client**, typ **Desktop app**, a pak **stáhni JSON** (Download JSON).
6. Napiš Claudovi *„Stáhl jsem JSON pro Google, nastav ho.“* Soubor přesune na správné místo (`.config/claude-google/credentials.json` v domovské složce). Klidně ho tam můžeš přesunout i sám.
7. V Claude Code napiš *„Vypiš moje Google tabulky.“* Otevře se prohlížeč s přihlášením Google:
   - Google upozorní, že aplikace není ověřená. To je v pořádku, je to tvoje vlastní aplikace. Klikni na **Advanced** a pak **Go to … (unsafe)**.
   - Povol přístup.

✅ **Ověření:** Claude vypíše seznam tvých tabulek.

## Volitelně: Facebook

Potřebuješ jen tehdy, když chceš, aby Claude četl starší posty na stránce, kterou spravuješ (třeba jako vzor pro nový report z turnaje), nebo na ni rovnou naplánoval nový post. **Nic se nezveřejní samo:** Claude post jen naplánuje, nejdřív za 10 minut a nejpozději za 30 dní, a jen po tvém OK. Do té doby ho v Meta Business Suite (Plánovač) můžeš upravit, přidat fotky nebo smazat.

Používá se společná Meta aplikace **Tagovačka** v režimu Live. Facebookové oprávnění ke stránkám má zatím jen základní úroveň (Standard Access), takže ji můžou používat jen lidé, které do ní správce přidá jako testery. Schválení od Meta (App Review) zatím potřeba není.

```
/plugin install facebook@claude-skills
```

### Jednou: správce aplikace

1. Na [developers.facebook.com](https://developers.facebook.com) se přihlas a zaregistruj se jako vývojář (zdarma).
2. **My Apps → Create App.** Název obecný (třeba `Claude Local Tool`), jako use case vyber **Spravujte vše na své stránce** (*Manage everything on your Page*). Nekombinuj ho s Facebook Loginem: s ním už stránkový use case přidat nejde a use case se nedá odebrat. Business portfolio připojovat nemusíš.
3. **Use cases → Spravujte vše na své stránce → Přizpůsobit**: u `pages_read_engagement` a `pages_manage_posts` dej **Přidat**. Jsou volitelná, bez toho je Explorer nenabídne.
4. **App roles → Roles → Add People → Testers**: přidej každého, kdo to bude používat.
5. **App settings → Basic**: tam je *App ID* a *App Secret*. Secret nikomu neposílej: má ho jen server Tagovačky, který za uživatele prodlužuje tokeny. Tady taky vyplň *Privacy Policy URL* a *User data deletion* (návod ke smazání dat), ikonu 1024×1024, kategorii a kontaktní e-mail. Bez nich aplikaci nejde přepnout do Live. Tagovačka má tyhle stránky na `https://tagovacka.cz/facebook-privacy` (smazání dat: `#smazani`).
6. **App settings → Basic**: do *App Domains* přidej `api-discgolf-tags.dominikvoda.com` (případně nejdřív *Add platform → Website* se *Site URL* `https://api-discgolf-tags.dominikvoda.com/`). Pak přidej produkt **Facebook Login for Business**. V jeho nastavení zapni *Strict Mode* a *Enforce HTTPS*, do *Valid OAuth Redirect URIs* dej `https://api-discgolf-tags.dominikvoda.com/api/facebook/callback` a *Require App Secret* nech vypnuté. V *Configurations* vytvoř konfiguraci s typem tokenu *User access token* a oprávněními `pages_show_list`, `pages_read_engagement` a `pages_manage_posts`. Její *Configuration ID* patří na server do `FACEBOOK_LOGIN_CONFIG_ID`.
7. V levém menu otevři **Publish** (Publikovat), projdi požadavky, které tam Meta ukáže, a aplikaci publikuj. Žádá-li u stránkových oprávnění App Review nebo ověření firmy, nepokračuj: to je až Advanced Access.

Rozhraní Meta se občas mění, takže názvy tlačítek se můžou trochu lišit.

### Každý uživatel

1. Přijmi pozvánku do aplikace na [developers.facebook.com/requests](https://developers.facebook.com/requests) (je potřeba být zaregistrovaný jako vývojář, zdarma).
2. Napiš Claudovi *„Nastav Facebook.“* Otevře ti v prohlížeči přihlášení k Facebooku. Povol aplikaci Tagovačka všechna oprávnění, která chce, a zaškrtni stránky, které chceš používat. Když prohlížeč napíše *Hotovo, můžeš zavřít okno*, je hotovo.
3. **Token nikdy nevkládej do chatu.**

Token při propojení jednou projde serverem Tagovačky, který ho prodlouží (k tomu je potřeba App Secret). Je tam zašifrovaný nejvýš 60 sekund a nikam se neukládá, viz [zásady ochrany údajů](https://tagovacka.cz/facebook-privacy).

**Když propojení v prohlížeči nejde** (třeba na počítači bez prohlížeče): v [Graph API Exploreru](https://developers.facebook.com/tools/explorer) vyber vpravo *Meta App* `Tagovačka` a *User Token*, přidej oprávnění `pages_show_list`, `pages_read_engagement` a `pages_manage_posts` a klikni na **Generate Access Token**. Token prodluž v [Access Token Debuggeru](https://developers.facebook.com/tools/debug/accesstoken) (**Debug**, dole **Extend Access Token**) a napiš Claudovi, ať použije ruční nastavení. Založí soubor `.config/claude-facebook/token.txt` v domovské složce a otevře ti ho. Prodloužený token do něj vlož, ulož a napiš Claudovi, že je hotovo.

✅ **Ověření:** Claude vypíše tvoje stránky s `expires never`. Takový token stránky nevyprší, dokud nezměníš heslo k Facebooku nebo nepřijdeš o roli na stránce. Pak stačí krok 2 zopakovat.

## Aktualizace

Nové verze se nestahují samy. Jednou za čas v Claude Code spusť:

```
/plugin marketplace update claude-skills
```

Nebo si zapni automatické aktualizace: napiš `/plugin`, otevři záložku **Marketplaces**, vyber `claude-skills` a zapni auto-update.

## Když něco nejde

| Problém | Řešení |
|---|---|
| Claude o pluginech neví | Restartuj Claude Code (`/exit`, pak znovu `claude`) a zkontroluj `/plugin`. |
| Přihlášení do Tagovačky selhává | Zkontroluj e-mail a heslo v `~/.tagovacka.json` (přihlas se s nimi na tagovacka.cz) a že soubor obsahuje rovné uvozovky `"`. |
| Přihlášení na ceskydiscgolf.cz selhává (401) | Zkontroluj login a heslo v `~/.ceskydiscgolf.json` (přihlas se s nimi na webu). Po pár neúspěších server na chvíli blokuje další pokusy. |
| „Missing Google OAuth client …“ | Ještě nemáš hotové [Google nastavení](#volitelně-google-tabulky-a-gmail), nebo `credentials.json` není v `~/.config/claude-google/`. |
| Google tě po týdnu znovu chce přihlásit | Aplikace je ve stavu Testing, oprav to podle bodu 4 v [Google nastavení](#volitelně-google-tabulky-a-gmail). Pak požádej Clauda, ať smaže staré Google tokeny a přihlásí tě znovu. |
| Facebook hlásí `code 190` nebo stránka `expires` s datem | Token vypršel nebo nebyl prodloužený. Zopakuj kroky 2–4 v [nastavení Facebooku](#volitelně-facebook). |
| Claude chce spustit příkaz a ptá se na povolení | To je normální. Čtení dat klidně povol, u zápisů si přečti, co dělá. |

**Kde je to vyzkoušené:** na macOS s Claude Code. Windows (Claude Code s Git Bashem) a Linux by měly fungovat stejně, ale vyzkoušené nejsou. Když narazíš na problém, [založ issue](https://github.com/dominikvoda/claude-skills/issues).

**Bezpečnost:** hesla a tokeny jsou jen u tebe v počítači (`~/.ceskydiscgolf.json`, `~/.tagovacka.json`, `~/.config/claude-google/` a `~/.config/claude-facebook/`), nikdy v tomhle repu. Nikomu je neposílej a nevkládej je do chatu.

## Codex a další AI agenti

Skilly jsou ve standardním formátu [Agent Skills](https://agentskills.io), takže fungují i v Codexu, Cursoru, Gemini CLI a dalších. Nainstaluješ je cross-agent instalátorem (potřebuje [Node.js](https://nodejs.org)):

```bash
npx skills add dominikvoda/claude-skills
```

Vyber skilly a agenta. `flighty-na-prani` a `tournament-email` potřebují i skill `ceskydiscgolf`, flighty navíc `gsheets`. Uzavření turnaje s rozhozy z Tagovačky potřebuje `ceskydiscgolf` i `tagovacka`, report z turnaje `ceskydiscgolf`, `facebook` a `gdrive`. Aktualizace stáhneš příkazem `npx skills update`. Vyzkoušené je to jen v Claude Code.

---

## English

Claude Code plugins for Czech disc golf tournament directors ([ceskydiscgolf.cz](https://ceskydiscgolf.cz)): registrations, propositions, flights, info e-mails and closing a tournament with podium tie-breaks read from [Tagovačka](https://tagovacka.cz), and post-tournament reports for a Facebook page. Plus Google Sheets and Drive (read-only), Google Forms (create and edit), Gmail and Facebook Pages.

```
/plugin marketplace add dominikvoda/claude-skills
/plugin install ceskydiscgolf@claude-skills     # also installs google (dependency)
/plugin install google@claude-skills            # Google only
/plugin install facebook@claude-skills          # Facebook Pages (optional)
```

Requirements: Python 3.9+, and [uv](https://docs.astral.sh/uv/) for the Google scripts.

| Credential | Location |
|---|---|
| ceskydiscgolf.cz login | `~/.ceskydiscgolf.json`, mode 600: `{"username": "...", "password": "..."}` |
| Tagovačka login (optional, read-only) | `~/.tagovacka.json`, mode 600: `{"email": "...", "password": "..."}` |
| Facebook page tokens (optional) | `~/.config/claude-facebook/`: `pages.json` (written by `fb.py connect`, which gets a long-lived token through the Tagovačka token broker), `token.txt` (only for the paste fallback, `fb.py setup`). One shared Meta app in Live mode with Standard Access; users are added as testers. Guide: [Volitelně: Facebook](#volitelně-facebook). |
| Google OAuth client + tokens | `~/.config/claude-google/` (`credentials.json`, `sheets-token.json`, `forms-token.json`, `gmail-token.json`). Bring your own Desktop OAuth client, see the Setup section of [`gsheets`](plugins/google/skills/gsheets/SKILL.md). |

Updates aren't automatic for third-party marketplaces: run `/plugin marketplace update claude-skills`.

Other agents (Codex, Cursor, Gemini CLI, …): `npx skills add dominikvoda/claude-skills`. The skills follow the [Agent Skills](https://agentskills.io) format; paths are relative to each skill's folder. Tested with Claude Code on macOS only.

## License

MIT
