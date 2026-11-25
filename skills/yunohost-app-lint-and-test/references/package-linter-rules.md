# `YunoHost/package_linter` Complete Rulebook & Anti-Patterns

Sources: `YunoHost/package_linter` (`tests/test_app.py`, `test_manifest.py`, `test_scripts.py`, `test_configurations.py`).

- **Critical (`✘✘✘`)**: Caps app quality at **Level 0** (exit code `1`).
- **Error (`✘`)**: Caps app quality below **Level 5** (exit code `1`).
- **Warning (`!`)**: Caps app quality below **Level 7**.
- **Info**: Advisory best practice.

---

## 1. Repository & File Layout Checks

- **[Error] Mandatory non-empty files**: `LICENSE` (no placeholder text), `README.md`, `manifest.toml`, `tests.toml`, `scripts/install`, `scripts/remove`, `scripts/upgrade`, `scripts/backup`, `scripts/restore`, `doc/DESCRIPTION.md` (no `"lorem ipsum"` or `"Some long and extensive description"`).
- **[Error] File encoding**: Every text file must be valid UTF-8.
- **[Error] Leftover template markers**: `REPLACEBYYOURAPP`, `config_panel.json`, `config_panel.toml` with `version = "0.1"`, or `YNH_CONFIG_` in `scripts/config`.
- **[Error] Bundled upstream sources**: Having `> 5` files in `sources/` is an Error (use `[resources.sources]` + `ynh_setup_source`).
- **[Warning] Leftover example/dummy files**: `config_panel.toml.example`, `doc/DISCLAIMER.md`, `doc/screenshots/example.jpg`, `"This is a dummy"` / `"Ceci est une fausse"` in `doc/`, `scripts/config` without `config_panel.toml`, `__DB_PWD__` in `doc/`, or screenshots `> 1024 KB`.

---

## 2. `manifest.toml` Checks

- **[Critical] Required top-level keys**: `packaging_format`, `id`, `name`, `description`, `version`, `maintainers`, `upstream`, `integration`, `install`, `resources`.
- **[Critical / Error] `integration.yunohost`**: `4.*` -> Critical; `11.0` -> Error. Use `">= 12.1.38"` (or `">= 12.1.17"`).
- **[Warning] `integration.helpers_version`**: Must be `"2.1"`.
- **[Error] `name` length**: Must be **<= 22 characters**.
- **[Error / Warning] `id`**: Must match `^[a-z0-9]((_|-)?[a-z0-9])+$` (Error); must not end in `_ynh` (Warning).
- **[Error / Warning] `description`**: Containing `"for yunohost"` -> Error; `< 5` or `> 150` chars -> Warning; starting with `id` or `name` -> Warning.
- **[Error] `version`**: Must match lowercase `<upstream>~ynh<N>` (`^[0-9a-z]*([\.+-][0-9a-z]*)*~ynh[0-9]*$`).
- **[Error / Warning] `[upstream]`**: Missing/invalid SPDX `license` (or `LicenseRef-*` without `license_url`); `example.com` in `website`/`demo` -> Error; `yunohost.org` in `admindoc` -> Error; `github.com` in `website` or duplicating `code` in `userdoc`/`admindoc` -> Warning.
- **[Error] `[install.<id>]` schema (`additionalProperties: false`)**: ONLY `type`, `default`, `example`, `optional`, `ask`, `help`, `choices`, `pattern`, `filter`, `visible` are valid in `manifest.toml`. Putting `min`, `max`, `step`, `yes`, `no`, `style`, `accept`, `redact`, `icon`, `enabled`, or `bind` causes `Error validating manifest using schema: Additional properties are not allowed`. Fix: remove those keys from `manifest.toml`, validate numeric bounds in `scripts/install` (or use `pattern.regexp`), and prefer `[resources.ports]` over an `[install.port]` question.
- **[Warning] `[install]` questions**:
  - Do **NOT** set `ask` on core questions: `("domain", "domain")`, `("path", "path")`, `("admin", "user")`, `("password", "password")`, `("init_main_permission", "group")`.
  - All custom questions **MUST** define `ask`.
  - `FIXME` comments anywhere in `manifest.toml` -> Warning.
- **[Warning] `[resources]`**:
  - `[resources.database]` **requires** `[resources.apt]` to appear **above** `[resources.database]` and include `mariadb-server` or `postgresql`.
  - Old PHP (`php7.4-*` -> Error; `php8.0-*`/`php8.1-*` -> Warning; unversioned `php-*` -> avoid; use `php8.2-*` or `php8.3-*`).
  - `resources.install_dir.dir` under `/opt/yunohost` -> Warning (use default `/var/www/__APP__`).
  - `integration.ldap = true` without `dc=yunohost,dc=org` in repo (or `ldap = false` *with* `dc=yunohost,dc=org`) -> Warning.

---

## 3. Lifecycle Script Checks (`scripts/*`)

| Severity | Forbidden Pattern | Required Replacement |
|---|---|---|
| **Critical** | `yunohost app setting ...` | `ynh_app_setting_set` / `_get` / `_set_default` / `_delete` |
| **Critical** | `var=$1` in `scripts/install` | Settings/questions are auto-loaded as `$var` |
| **Error** | `ynh_abort_if_errors`, `set -eu`, `set -u` in standard scripts | Omit completely (only `scripts/config` uses `ynh_abort_if_errors`) |
| **Error** | `apt install` / `apt-get` / `ynh_package_install` | `[resources.apt]` in `manifest.toml` |
| **Error** | `rm -rf` / `rm -r` / `rm -fr` | `ynh_safe_rm` (one path per call) |
| **Error** | `systemctl restart nginx` / `service nginx restart` | `ynh_systemctl --service=nginx --action=reload` |
| **Error** | `dd if=/dev/urandom` / `openssl rand` | `ynh_string_random` |
| **Error** | `exit` | `ynh_die "message"` |
| **Error** | `source _common.sh` in `backup` or `restore` | `source ../settings/scripts/_common.sh` (before helpers!) |
| **Error** | `yunohost service add` without `yunohost service remove` in `remove` | Remove service in `scripts/remove` and keep `yunohost service add` flags identical across `install`, `upgrade`, `restore` |
| **Error** | Editing `/etc/ssowat/conf.json.persistent` or `skipped_uris` | `[resources.permissions]` |
| **Warning** | Sourcing files *after* `source /usr/share/yunohost/helpers` | Source `_common.sh` **before** helpers |
| **Warning** | Removing `/var/log/$app` or `$data_dir` in `scripts/remove` | Handled by YunoHost core (`--purge` for `$data_dir`) |
| **Warning** | `ynh_script_progression` in `_common.sh` or `backup` | Use `ynh_print_info` in `backup` |
| **Warning** | Stopping/starting services in `scripts/backup` | Do not stop services in `backup` (`ynh_backup` only declares paths) |
| **Warning** | Raw `systemctl start/stop/restart` | `ynh_systemctl --service="$app" --action="..."` |
| **Warning** | `systemctl enable` without `--quiet` | `systemctl enable "$app.service" --quiet` |
| **Warning** | `chmod 777` / `chmod o+w` | Use `$app` owner/group and `400`/`600`/`750` |
| **Warning** | Reloading `nginx` at end of `install`/`upgrade`/`remove` | `ynh_config_add_nginx` / `ynh_config_remove_nginx` already reload `nginx` (only reload in `restore`) |
| **Warning** | Calling resource-deprecated helpers (`ynh_nodejs_install`, `ynh_mysql_setup_db`, `ynh_system_user_create`, `ynh_find_port`, etc.) | Declare in `[resources.*]` |

---

## 4. NGINX & Systemd Configuration Checks (`conf/*`)

- **[Error] NGINX alias path traversal**: `location __PATH__` (no `/`) + `alias __INSTALL_DIR__/;` (with `/`) allows reading `/var/www/myapp_other`! Always use `location __PATH__/ { alias __INSTALL_DIR__/; ... }`.
- **[Error] `add_header` inside `location`**: Use `more_set_headers "Header-Name: value";`.
- **[Error] `if ($scheme = http)`**: Handled globally by YunoHost.
- **[Warning] Missing `proxy_params_*` / `fastcgi_params_*` (YunoHost >= 12.1.38)**:
  - `integration.sso = true` **must** use `include proxy_params_with_auth;` or `include fastcgi_params_with_auth;`.
  - `integration.sso = false` / `"not_relevant"` **must** use `include proxy_params_no_auth;` or `include fastcgi_params_no_auth;`.
- **[Info] Redundant `proxy_set_header` / `fastcgi_param` in `conf/*nginx*.conf`**:
  - Remove manual definitions of params already provided by `proxy_params_*` / `fastcgi_params_*`: `Host`, `X-Real-IP`, `X-Scheme`, `X-Forwarded-*`, `Upgrade`, `Connection`, `REMOTE_USER`, `PATH_INFO`, and `SCRIPT_FILENAME`. Only keep an explicit override (e.g. custom `SCRIPT_FILENAME`) if the app requires a non-default value.
- **[Error] Secrets in systemd `Environment=`**: Any `Environment=` line matching `pass|secret|key` is an Error; move secrets to `EnvironmentFile=__INSTALL_DIR__/.env` (`chmod 400`).
- **[Warning / Info] Service user in EVERY `conf/*.service` file**: `package_linter` checks **all** `conf/*.service` files (except `*override*`) containing `[Unit]`, including helper/oneshot units like `reload.service`. Never omit `User=` and never run as `root` or `www-data` — always specify `User=__APP__` (and `Group=__APP__`). Missing `User=` is a **Warning** for regular services and **Info** for `Type=oneshot`.
- **[Info] Systemd security hardening in EVERY `conf/*.service` file**: Include the `example_ynh` baseline (`CapabilityBoundingSet=~...`, `ProtectSystem=...`/`Protect*`, `SystemCallFilter=~...`, `PrivateTmp=yes`, `NoNewPrivileges=yes`, `PrivateDevices=yes`) in **all** `conf/*.service` files (not only `systemd.service`).
- **[Info] Binding to `0.0.0.0` / `::` in `conf/*`**: Change internal app daemons behind NGINX to bind `127.0.0.1` (or `::1`) so NGINX/SSOwat cannot be bypassed via public IP/IPv6. For intentionally public non-HTTP services (e.g. VPN, TURN, MTProto proxy) declaring `exposed = "TCP"|"UDP"|"Both"` in `[resources.ports]`, confirm it is intentional and ignore this `Info` notice.
