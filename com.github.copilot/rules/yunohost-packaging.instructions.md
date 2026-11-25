---
name: "YunoHost Packaging v2 & Helpers v2.1 Rules"
description: "Use when editing YunoHost app package files (*_ynh): manifest.toml, tests.toml, config_panel.toml, scripts/{install,upgrade,remove,backup,restore,change_url,config,_common.sh}, conf/*.conf, conf/*.service, doc/*.md, or hooks/*."
applyTo: "**/manifest.toml,**/tests.toml,**/config_panel.toml,**/scripts/_common.sh,**/scripts/install,**/scripts/upgrade,**/scripts/remove,**/scripts/backup,**/scripts/restore,**/scripts/change_url,**/scripts/config,**/conf/*.conf,**/conf/*.service"
---

# YunoHost Packaging v2 & Helpers v2.1 Essential Rules

## `manifest.toml`
- Require all 10 top-level keys: `packaging_format = 2`, `id`, `name` (max **22** chars), `description` (max 150 chars, never say `"for YunoHost"` or start with app name), `version` (`<lowercase_ver>~ynh<N>`), `maintainers = [...]` (array), `[upstream]`, `[integration]`, `[install]`, `[resources]`.
- In `[integration]`, use `yunohost = ">= 12.1.38"` (or `">= 12.1.17"`) and `helpers_version = "2.1"`. Size strings (`disk`, `ram.build`, `ram.runtime`) must use `[kKmMgG]` without `B` (e.g. `"50M"`, `"1G"`, NEVER `"50MB"`).
- Do NOT define `ask` on core-managed install questions: `domain` (`domain`), `path` (`path`), `admin` (`user`), `password` (`password`), `init_main_permission` (`group`). Note that `password` and `init_*_permission` are NOT auto-saved to `settings.yml`.
- `[install.<id>]` in `manifest.toml` has `additionalProperties: false` — ONLY these 10 keys are allowed: `type`, `default`, `example`, `optional`, `ask`, `help`, `choices`, `pattern`, `filter`, `visible`. NEVER use `min`, `max`, `step`, `yes`, `no`, `style`, `accept`, `redact`, `icon`, `enabled`, or `bind` in `manifest.toml` (validate numeric bounds in `scripts/install`, or use `[resources.ports]` instead of a port install question).
- If `[resources.database]` is used, `[resources.apt]` MUST appear **before** `[resources.database]` and explicitly include `mariadb-server` (for `mysql`) or `postgresql` (for `postgresql`).
- Subkeys under `apt.extras.<k>`, `permissions.<k>`, and `ports.<k>` must be `>= 2` chars (`^[a-z0-9][a-z0-9_]+$`, no hyphens). Valid `sources.<id>.format` values: `tar.bz2`, `tar.gz`, `tar.xz`, `tar.zst`, `xz`, `zip`, `zst`, `docker`, `whatever` (NEVER `script`).

## Lifecycle Scripts (`scripts/*`)
- Source order: `source _common.sh` then `source /usr/share/yunohost/helpers` in `install`, `upgrade`, `remove`, `change_url`. In `backup` and `restore`, ALWAYS use `source ../settings/scripts/_common.sh` BEFORE `source /usr/share/yunohost/helpers`.
- NEVER use `ynh_abort_if_errors` or `set -eu` in `install`, `upgrade`, `remove`, `backup`, `restore`, `change_url`, or `_common.sh` (only `scripts/config` uses `ynh_abort_if_errors`).
- NEVER use `apt install`, `rm -rf` (use `ynh_safe_rm` one path per call), `exit` (use `ynh_die "msg"`), `yunohost app setting` (use `ynh_app_setting_set` / `_get` / `_set_default` / `_delete`), `openssl rand` (use `ynh_string_random`), or `systemctl restart nginx` (use `ynh_systemctl --service=nginx --action=reload`).
- NEVER use `ynh_script_progression` in `_common.sh` or `backup` (use `ynh_print_info` in `backup`). In v2.1, `ynh_script_progression "Message"` takes a single positional string—NEVER pass `--message=`, `--weight=`, `--time`, or `--last`.
- Use exact v2.1 helper names and argument styles:
  - Keyword (`--flag=val`): `ynh_setup_source`, `ynh_config_add`, `ynh_config_add_systemd`, `ynh_systemctl`, `ynh_config_add_fail2ban`, `ynh_replace`, `ynh_replace_regex`, `ynh_app_setting_*`, `ynh_string_random`.
  - Positional / zero-arg: `ynh_config_add_nginx`, `ynh_config_remove_nginx`, `ynh_config_change_url_nginx`, `ynh_config_add_phpfpm`, `ynh_config_remove_phpfpm`, `ynh_config_remove_systemd [service]`, `ynh_config_add_logrotate [path]`, `ynh_config_remove_logrotate`, `ynh_config_remove_fail2ban`, `ynh_safe_rm path`, `ynh_backup path`, `ynh_restore path`, `ynh_restore_everything`, `ynh_mysql_db_shell [db]`, `ynh_mysql_dump_db [db]`, `ynh_psql_db_shell [db]`, `ynh_psql_dump_db [db]`, `ynh_exec_as_app cmd ...`, `ynh_composer_exec cmd ...`, `ynh_app_upgrading_from_version_before ver~ynhN`.

## NGINX & Systemd (`conf/*`)
- Bind internal app daemons to `127.0.0.1` (or `::1`), NEVER `0.0.0.0` or `::` (which lets clients bypass NGINX/SSOwat). Never set `exposed = true` on internal HTTP reverse-proxy ports in `[resources.ports]`. Only intentionally public non-HTTP services (e.g. VPN, TURN, MTProto proxy) with `exposed = "TCP"|"UDP"|"Both"` should bind `0.0.0.0`/`::`.
- In `conf/*nginx*.conf` (YunoHost >= 12.1.38): include `proxy_params_with_auth;` (when `integration.sso = true`) or `proxy_params_no_auth;` (when `sso = false` / `"not_relevant"`), or `fastcgi_params_with_auth;` / `fastcgi_params_no_auth;`. Do NOT manually redefine params already set by those snippets (`SCRIPT_FILENAME`, `PATH_INFO`, `REMOTE_USER`, `Host`, `X-Real-IP`, `X-Forwarded-*`, `Upgrade`, `Connection`) unless a custom override is strictly required. Never use `add_header` inside `location` (use `more_set_headers "Header: value";`). Always pair `location __PATH__/ {` with `alias __INSTALL_DIR__/;` (both with trailing `/`).
- In **every** `conf/*.service` file (including secondary/helper/oneshot units like `reload.service`): always specify `User=__APP__` and `Group=__APP__`, include the full `example_ynh` systemd sandboxing baseline (`PrivateTmp=yes`, `ProtectSystem=...`, `SystemCallFilter=...`, `CapabilityBoundingSet=...`), and NEVER put passwords/secrets/keys directly in `Environment=` (use `EnvironmentFile=` with `chmod 400` or `600`).
