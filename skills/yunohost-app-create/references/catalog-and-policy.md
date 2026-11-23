# Publishing on the YunoHost Catalog & Editorial Policy Reference

Sources: `doc.yunohost.org/en/dev/packaging/publish`, `policy`, and `YunoHost/apps` (`apps.toml`, `categories.toml`, `antifeatures.toml`).

---

## 1. Publishing Checklist (`YunoHost/apps`)

To add a working app to the official YunoHost catalog (`https://github.com/YunoHost/apps`):
1. Ensure the package passes `package_linter` with zero Critical/Error issues and installs/upgrades/backs-up/restores cleanly.
2. Add a square (or near-square) logo at `logos/<app_id>.png` in `YunoHost/apps` (compressed to minimal size).
3. Add an alphabetical `[<app_id>]` entry to `apps.toml` in `YunoHost/apps` and open a Pull Request:

```toml
[myapp]
url = "https://github.com/YunoHost-Apps/myapp_ynh"
state = "working"                        # "working" | "inprogress" | "notworking"
category = "productivity_and_management"
subtags = ["task"]
potential_alternative_to = ["Trello", "Asana"]
# antifeatures = ["arbitrary-limitations"] # Omit if none
```

- **NEVER manually add `level`, `added_date`, or `deprecated_date`** in `apps.toml` — `yunohost-bot` updates `level` (`0..8`) automatically from CI results.
- Transferring your repo to the **`YunoHost-Apps`** GitHub organization (ask in the [App Packaging Matrix/XMPP chatroom](https://doc.yunohost.org/en/community/chat_rooms)) unlocks **Level 6+**, `yunohost-bot` README generation, `!testme` PR CI, and daily `autoupdate_app_sources` PRs!

---

## 2. All Valid Catalog Categories & Subtags (`categories.toml`)

| `category` | Allowed `subtags` |
|---|---|
| `synchronization` | `files`, `calendar`, `contacts`, `password` |
| `publishing` | `website`, `blog`, `wiki`, `ecommerce`, `analytics`, `static_site_generator` |
| `communication` | `chat`, `forum`, `email`, `meeting` |
| `office` | `text`, `spreadsheet`, `impress`, `draw`, `mindmap` |
| `productivity_and_management` | `task`, `poll`, `accounting`, `business_and_ngos` |
| `small_utilities` | `pastebin`, `url_shortener`, `proxy`, `files` |
| `reading` | `rssreader`, `books` |
| `education` | *(no subtags)* |
| `multimedia` | `mediacenter`, `download`, `music`, `pictures`, `videos` |
| `social_media` | `microblogging`, `blogging`, `events`, `videos`, `pictures`, `music` |
| `games` | *(no subtags)* |
| `dev` | `forge`, `skeleton`, `programming`, `design` |
| `system_tools` | `backup`, `monitoring`, `network`, `db` |
| `iot` | *(no subtags)* |
| `wat` | *(no subtags)* |

---

## 3. All Valid Catalog Anti-Features (`antifeatures.toml`)

When applicable, list the key in `apps.toml` (`antifeatures = [...]`) AND add an explanation under `[antifeatures]` in the package's `manifest.toml`:

- `tracking`: Reports/tracks user activity without opt-in consent
- `non-free-network`: Depends on or promotes a proprietary network service
- `non-free-addons`: Promotes proprietary plugins/extensions
- `non-free-dependencies`: Requires non-free runtime dependencies
- `non-free-assets`: Bundles non-free media/artwork
- `bad-security-reputation`: Poor upstream security track record or insecure dependencies
- `deprecated-software`: Upstream project is unmaintained/archived
- `package-not-maintained`: YunoHost wrapper is unmaintained (seeking maintainer; blocks Level 8)
- `paid-content`: Promotes or depends on paid services
- `arbitrary-limitations`: Open-core or artificial feature/seat caps
- `replaced-by-another-app`: Superseded by another app (blocks Level 8)
- `alpha-software`: Early-stage/unstable upstream software (blocks Level 8)
- `not-totally-free-upstream`: Source-available / ethical / restricted license (e.g. BSL, ACSL, HL3)
- `not-totally-free-package`: Restricted license on the YunoHost package itself

---

## 4. YunoHost Catalog Inclusion & Generative AI Policy

- **FOSS License Requirement**: Upstream software must generally be Free & Open Source Software. Gray-area source-available or ethical licenses are evaluated case-by-case with `not-totally-free-upstream`.
- **Excluded Categories**: Apps promoting cryptocurrencies, futile/extractive AI hype, stalking/surveillance, overly complex enterprise stacks disproportionate to YunoHost servers, or hyper-niche single-user scripts. (Excluded apps can still be installed directly via `yunohost app install <git_url>` or custom catalogs in `/etc/yunohost/apps_catalog.yml`.)
- **Generative AI Policy**: Packages with hallucinated `ynh_*` helpers, non-standard directory structures, or noisy AI-generated comments are rejected. Always keep code clean, idiomatic to `example_ynh`, linted, tested, and transparent so the human maintainer understands and owns every line.
