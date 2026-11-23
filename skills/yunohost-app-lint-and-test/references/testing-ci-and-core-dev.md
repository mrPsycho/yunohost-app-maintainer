# Testing (`tests.toml`, `package_check`, Quality Levels), `ynh-dev` & Core Reference

Sources: `doc.yunohost.org/en/dev/packaging/test`, `core/`, `core/architecture`, `core/devenv`, `core/ynh_core`, `core/ynh_admin`, `core/maindomain`, `doc`, `translation`, and `misc/*`.

---

## 1. `tests.toml` Complete Reference (`tests.v1.schema.json`)

```toml
#:schema https://raw.githubusercontent.com/YunoHost/apps/main/schemas/tests.v1.schema.json

test_format = 1.0

[default]
    # Custom install args ONLY needed for questions without a default in manifest.toml:
    # args.custom_choice = "foo"

    # Shell setup before install / upgrade (rarely needed, e.g. companion app):
    # preinstall = """
    # sudo yunohost app install companion_app
    # """

    # Test real upgrades from previous production commit(s) on main:
    # test_upgrade_from.00a1a6e7.name = "Upgrade from 1.5.0"

    # HTTP assertions run after install, upgrade, restore, and change_url:
    [default.curl_tests]
    home.path = "/"
    home.expect_title = "My App"
    home.expect_return_code = 200

    dashboard.path = "/dashboard"
    dashboard.logged_on_sso = true
    dashboard.expect_content = "Welcome"
    dashboard.expect_return_code = [200, 302]

# Optional extra suite (note: `only` is allowed ONLY on non-default suites!):
# [alt_mode]
#     only = ["install.subdir"]
#     args.mode = "advanced"
```

### Auto-Generated `package_check` Test IDs
- `package_linter` (always run)
- `install.root` (webapp at `domain.tld/`)
- `install.subdir` (webapp with `[install.path]` at `domain.tld/path`)
- `install.nourl` (non-webapp without NGINX config)
- `install.private` (`init_main_permission=all_users`)
- `install.multi` (`integration.multi_instance = true`)
- `backup_restore`
- `upgrade` (same-version upgrade) & `upgrade.<commit>` (from `test_upgrade_from`)
- `change_url` (when `scripts/change_url` exists)

*(Avoid `exclude = [...]` unless an install topology is genuinely impossible upstream.)*

---

## 2. YunoHost App Quality Levels (`0`–`8`)

| Level | Qualification Criteria |
|---|---|
| **0** | Broken install OR Critical `package_linter` issue |
| **1** | At least 1 install scenario passes + 0 Critical linter issues |
| **2** | All install scenarios pass (`root`, `subdir`, `private`, `multi`) |
| **3** | Level 2 + same-version `upgrade` passes |
| **4** | Level 3 + `backup_restore` passes *(Levels <= 4 show low-quality warning!)* |
| **5** | Level 4 + **0 Errors** in `package_linter` |
| **6** | Level 5 + hosted in the community **`YunoHost-Apps`** GitHub org |
| **7** | Level 6 + **all** tests pass (including `upgrade.<commit>` & `change_url`) + **0 Warnings** in `package_linter` |
| **8** | Level 7 + sustained `>= Level 5` for ~1 year and not tagged `deprecated-software` / `alpha-software` / `package-not-maintained` / `replaced-by-another-app` |

---

## 3. Running `package_linter`, `package_check` & `ynh-dev` Locally

### `package_linter`
```bash
git clone https://github.com/YunoHost/package_linter
python3 -m venv package_linter/venv
package_linter/venv/bin/pip install -r package_linter/requirements.txt
package_linter/venv/bin/python package_linter/package_linter.py /path/to/myapp_ynh
```

### `package_check` (Incus Container Integration Runner)
```bash
# Setup Incus remote once:
sudo apt install incus && sudo usermod -a -G incus-admin "$USER"
incus admin init
incus remote add yunohost https://repo.yunohost.org/incus --protocol simplestreams --public

# Run full test suite (use -i to pause before removal or -e to pause on error):
git clone https://github.com/YunoHost/package_check
./package_check/package_check.sh -e /path/to/myapp_ynh
```

### `ynh-dev` (Core & App Interactive Container Environment)
```bash
curl https://raw.githubusercontent.com/yunohost/ynh-dev/master/deploy.sh | bash
cd ynh-dev
./ynh-dev start
# Inside container:
yunohost tools postinstall
```
*(Tip for test VMs/containers: disable strict password checks with `sudo yunohost settings set security.password.user.strength -v -1` and `security.password.admin.strength -v -1`.)*

---

## 4. YunoHost Core Architecture Overview (`doc.yunohost.org/en/dev/core/`)

Useful when debugging how YunoHost executes app scripts, hooks, forms, or SSOwat:

1. **`moulinette`** (`YunoHost/moulinette`): Python framework turning a declarative YAML **actionsmap** into both the `yunohost` CLI and `yunohost-api` REST server, with auth and i18n (`m18n`).
2. **`yunohost`** (`YunoHost/yunohost`):
   - `data/actionsmap/yunohost.yml` -> maps `yunohost <cat> <action>` and `/yunohost/api/...` to `src/yunohost/<cat>.py` (`<cat>_<action>(...)`). **Always run `systemctl restart yunohost-api`** after editing Python code or actionsmap!
   - `src/yunohost/utils/resources.py` -> provisions/deprovisions `[resources.*]` from `manifest.toml`.
   - `src/yunohost/utils/form.py` -> evaluates `[install]` questions and `config_panel.toml` forms.
   - `helpers/helpers.v2.1.d/` -> Bash helpers sourced by `/usr/share/yunohost/helpers`.
   - `hooks/` & `conf/` -> system-wide `conf_regen` templates (NGINX, Postfix, Dovecot, slapd, DNS, nftables/iptables).
   - Core PR convention: branches `enh-<issue>-desc` or `fix-<issue>-desc`, PR titles `[enh] ...` or `[fix] ...` targeting `unstable`, PEP 8 + type hints, raise `YunohostError(...)`, i18n keys in `locales/en.json` (`m18n.n('key')`).
3. **`ssowat`** (`YunoHost/ssowat`): NGINX Lua access-control & SSO header middleware driven by `/etc/ssowat/conf.json`.
4. **`yunohost-portal`** & **`yunohost-admin`**: End-user SSO portal (served on the server's **main domain**, which also backs hostname, mail EHLO/TLS, Local CA, and root mail aliases) and WebAdmin UI.
5. **Translations & Documentation**:
   - Core, WebAdmin, Portal, and Admin Docs are translated via **Weblate** (`https://translate.yunohost.org`).
   - App packages (`manifest.toml`, `config_panel.toml`, `doc/*_<lang>.md`) are translated directly via Git PRs in each `<app>_ynh` repository.
   - Documentation lives in `YunoHost/doc` (Docusaurus `.mdx`; preview with `npm ci && npm run start`).
