# Config Panels, Form Field Types, Hooks & App Documentation Reference

Sources: `doc.yunohost.org/en/dev/packaging/doc`, `advanced/config_panels`, `advanced/hooks`, `core/forms`, and `YunoHost/apps/schemas/config_panel.v1.schema.json`.

---

## 1. Config Panels (`config_panel.toml` + Optional `scripts/config`)

Exposes app settings in `WebAdmin > Apps > <App> > Config Panel` and CLI `yunohost app config`.

```toml
#:schema https://github.com/YunoHost/apps/raw/main/schemas/config_panel.v1.schema.json
version = "1.0"

[main]
name.en = "Main configuration"
services = ["__APP__"] # Reloaded/restarted automatically when any setting in this panel changes

    [main.general]
    name.en = "General settings"
    optional = false

        [main.general.signup_enabled]
        ask.en = "Allow public user registration"
        type = "boolean"
        yes = "true"
        no = "false"
        bind = "ENABLE_SIGNUP:__INSTALL_DIR__/.env"
```

### Key Rules & `bind` Modes
1. **Unique Short Keys**: Every option's leaf key (e.g. `signup_enabled`) **must be globally unique** across the entire `config_panel.toml`.
2. **Forbidden Short Keys**: `old`, `file_hash`, `types`, `binds`, `formats`, `changed`.
3. **Initialize in `install`/`upgrade`**: Every bound option (except `bind = "null"`) should also be initialized in `settings.yml` during `install` and `upgrade` (`ynh_app_setting_set_default`) so `ynh_config_add` templates don't overwrite config panel changes on upgrade!
4. **All `bind` Syntaxes**:
   - *(omitted)* or `"settings"` -> reads/writes `/etc/yunohost/apps/$app/settings.yml` only.
   - `":__INSTALL_DIR__/config.yml"` -> reads/writes `<short_key>` in file (YAML, TOML, JSON, INI, `.env`, PHP `$var = ...`, Python `KEY = ...`) **and** `settings.yml`.
   - `"SIGNUP_ALLOWED:__INSTALL_DIR__/.env"` -> maps `<short_key>` to `SIGNUP_ALLOWED` in `.env` **and** `<short_key>` in `settings.yml`.
   - `"smtp>host:__INSTALL_DIR__/config.toml"` -> maps `<short_key>` to `host` appearing after `smtp` section/parent.
   - `"__INSTALL_DIR__/public/logo.png"` *(no colon `:`)* -> binds to the **entire file** (for `type = "file"` or `type = "text"`). Note: `accept` in schema is an array of extensions, e.g. `accept = [".png", ".jpg"]`.
   - `"null"` -> virtual/ephemeral option handled by custom functions in `scripts/config` (or `type = "button"` actions).

### Custom Logic & Actions in `scripts/config`
Only create `scripts/config` if declarative `bind` is insufficient (`package_linter` warns if `scripts/config` exists without `config_panel.toml`!):
- `get__<short_key>()`: Echo current value (quote `#` strings like `"\"$color\""` because output is parsed as YAML, echo `YNH_NULL` if unset, or echo multi-line YAML overriding `style:`, `value:`, `ask:`).
- `validate__<short_key>()`: Echo error string if invalid; output nothing if valid.
- `set__<short_key>()`: Runs only when changed (`${old[$short_key]}` has previous value, `$<short_key>` has new value). Remember to call `ynh_app_setting_set --key=<short_key> --value="$<short_key>"`!
- `run__<action_id>()`: Triggered by a `[panel.section.<action_id>]` option with `type = "button"` (or `yunohost app action run $app <action_id>`). All sibling inputs in that section are available as `$<sibling_key>`.
- Always end `scripts/config` with `ynh_app_config_run "$1"`.

---

## 2. Complete YunoHost Form Option Types (`forms.mdx`)

Used in `[install.<id>]` (`manifest.toml`) and `[panel.section.<id>]` (`config_panel.toml`):

| `type` | Specific Properties & Notes |
|---|---|
| `string` | Single-line text; supports `pattern` (`pattern.regexp = '...'`, `pattern.error = "..."`), `example`, `redact` |
| `text` | Multi-line textarea; supports `pattern` |
| `password` | Enforces password policy (>= 8 chars); `redact` forced `true`; `example` **forbidden**; not saved to `settings.yml` on install |
| `boolean` | `default` must be boolean `true`/`false` in `manifest.toml`; in `config_panel.toml` supports `yes = "true"` / `no = "false"` |
| `number` | Integer; supports `min`, `max`, `step` |
| `range` | Slider integer; supports `min`, `max`, `step` |
| `select` | Single choice; `choices = ["a", "b"]` or `choices.key_a = "Label A"` (keys `[a-zA-Z0-9_]+`, no `-`!) |
| `tags` | Multi-value comma-separated output `"a,b"`; optional `choices`, `pattern`, `icon` |
| `domain` | Registered YunoHost domain selector (do not set `default` or `ask` on `[install.domain]`) |
| `path` | URL path `/...` (e.g. `default = "/myapp"`) |
| `user` | Existing YunoHost user selector (do not set `default` or `ask` on `[install.admin]`) |
| `group` | YunoHost group selector (`"visitors"`, `"all_users"`, `"admins"`, custom groups) |
| `app` | Installed YunoHost app selector; optional `filter = "is_webapp"` (`JSExpression`) |
| `email` | Validated email address |
| `url` | Full URL (`https://...`) |
| `date` | ISO `"YYYY-MM-DD"` |
| `time` | 24h `"HH:MM"` |
| `color` | Hex color `"#2B748B"` |
| `file` | File upload / path; `accept = [".png", ".conf"]` |
| `alert` | Readonly banner; `style = "info" \| "success" \| "warning" \| "danger"` (in `config_panel.v1.schema.json`: `"info"`, `"danger"`, `"success"`), `ask` supports Markdown |
| `markdown` | Readonly Markdown text block in `ask` |
| `button` | **Config panels only**: triggers `run__<id>()` in `scripts/config`; `style`, `enabled` (`bool` or `JSExpression`), `icon` |

### `visible` & `enabled` Dynamic `JSExpression`
Can reference **preceding** options in the same form/section using `==`, `!=`, `>`, `>=`, `<`, `<=`, `!`, `&&`, `||`, and `match(opt_id, '^regex$')` (e.g. `visible = "auth_mode == 'oidc'"`).

---

## 3. YunoHost Hooks (`hooks/<hook_name>`)

Place executable bash scripts inside `hooks/` at the package root (do NOT manually copy files into `/etc/yunohost/hooks.d/`!):

| Hook Filename in `hooks/` | Trigger | Key Variables / Args |
|---|---|---|
| `post_user_create` | `yunohost user create` | `YNH_USER_USERNAME`, `YNH_USER_MAIL`, `YNH_USER_PASSWORD` |
| `post_user_update` | `yunohost user update` | `YNH_USER_USERNAME`, `YNH_USER_PASSWORD`, `YNH_USER_MAILS`, `YNH_USER_MAILFORWARDS`, `YNH_USER_MAILQUOTA` |
| `post_user_delete` | `yunohost user delete` | `$1` = username, `$2` = `True` if `--purge` |
| `post_app_addaccess` | `yunohost user permission add` | `$1` = app, `$2` = users CSV, `$3` = sub-perm, `$4` = groups CSV |
| `post_app_removeaccess` | `yunohost user permission remove` | `$1` = app, `$2` = users CSV, `$3` = sub-perm, `$4` = groups CSV |
| `post_domain_add` / `post_domain_remove` | `yunohost domain add/remove` | `$1` = domain |
| `post_cert_update` | `yunohost domain cert update` | `$1` = domain (ideal for copying TLS certs to XMPP/TURN/mail/VPN daemons!) |
| `custom_dns_rules` | `yunohost domain dns suggest` | `base_domain`, `suffix`, `$1` = base domain; stdout JSON array `[{"type":"SRV",...}]` |
| `post_app_install` / `upgrade` / `remove` / `change_url` | Other app lifecycle events | `YNH_APP_ID`, `YNH_APP_INSTANCE_NAME`, etc. |
| `post_iptable_rules` | `yunohost firewall reload` | `$1` = UPnP bool, `$2` = IPv6 bool |

---

## 4. Documenting Apps (`doc/` & Automatic `README.md`)

- **`doc/DESCRIPTION.md`** (**Mandatory**): Multi-paragraph Markdown overview and bullet list of features shown in the app catalog and generated `README.md`. Never leave dummy/lorem-ipsum text! Localize as `doc/DESCRIPTION_fr.md`, etc.
- **`doc/ADMIN.md`**: YunoHost-specific administration notes shown in WebAdmin app info (CLI commands, OIDC setup, cron notes, paths). Supports `__DOMAIN__`, `__PATH__`, `__INSTALL_DIR__`, `__DATA_DIR__`, `__APP__`, and any `__SETTING__` (NEVER put `__DB_PWD__` here!).
- **`doc/PRE_INSTALL.md` / `POST_INSTALL.md` / `PRE_UPGRADE.md` / `POST_UPGRADE.md`**: Shown as interactive modals/CLI prompts. **Delete** any file you don't actually need (never leave dummy `example_ynh` files or obsolete `doc/DISCLAIMER.md`!).
- **`doc/PRE_UPGRADE.d/<version>.md` & `POST_UPGRADE.d/<version>.md`**: Shown only when upgrading from `< <version>` to `>= <version>` (e.g. `doc/PRE_UPGRADE.d/2.0.0~ynh1.md`).
- **`doc/screenshots/`**: Put 1+ real `.png`/`.jpg`/`.webp` screenshots (`< 512 KB` ideal, `< 1024 KB` max; remove `example.jpg`!). Subfolders `doc/screenshots/aux/` are ignored by the catalog gallery and can store diagrams linked from `ADMIN.md`.
- **`README.md`**: On `YunoHost-Apps`, `yunohost-bot` overwrites `README.md` automatically on push (unless commit message includes `no_readme`). Keep the standard generated format so `package_linter` doesn't warn.
