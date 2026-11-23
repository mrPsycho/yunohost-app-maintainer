---
name: yunohost-app-create
description: 'Create new YunoHost application packages (*_ynh) from scratch using Packaging v2, manifest.toml resources, Helpers v2.1, NGINX/systemd/PHP-FPM templates, SSOwat/LDAP integration, config_panel.toml, hooks, doc/ pages, and YunoHost/apps catalog registration. Use when packaging a new app for YunoHost, writing manifest.toml or lifecycle scripts, integrating LDAP/SSO, adding a config panel or hook, or publishing an app to the YunoHost catalog.'
argument-hint: '<app-id or upstream repo URL> [stack: proxy|php|python|nodejs|go|ruby|static]'
---

# Create a YunoHost Application Package (Packaging v2 / Helpers v2.1)

Package self-hosted applications for YunoHost following the official [YunoHost Packaging Documentation](https://doc.yunohost.org/en/dev/packaging/), `YunoHost/example_ynh` conventions, and Level 7/8 `package_linter` standards.

## When to Use

- Packaging a new application repository (`<id>_ynh`) for YunoHost
- Authoring `manifest.toml`, `[install]` questions, or `[resources.*]` declarations
- Writing `scripts/{_common.sh,install,upgrade,remove,backup,restore,change_url,config}` with YunoHost Helpers v2.1
- Configuring NGINX (`proxy_params_*`, `fastcgi_params_*`), Systemd sandboxing, PHP-FPM, Fail2Ban, or Logrotate
- Integrating SSOwat HTTP headers, LDAP (`dc=yunohost,dc=org`), `config_panel.toml`, `hooks/`, or `doc/*.md`
- Submitting an app to the official `YunoHost/apps` catalog (`apps.toml` + `logos/<id>.png`)

## Packaging Philosophy & Community Rules

1. **Zero manual post-install config**: Automate DB setup, admin user creation, ports, and URLs via `ynh_config_add`, CLI tools (`ynh_exec_as_app`), or `ynh_local_curl`. Never put `__DB_PWD__` in `doc/` expecting the admin to paste database credentials.
2. **Keep `[install]` minimal**: Ask only essential non-technical questions (`domain`, `path`, `init_main_permission`, plus `admin`/`password` if needed).
3. **Follow `example_ynh` style**: Use standard `#=================================================` banners, standard variable names (`$app`, `$domain`, `$path`, `$install_dir`, `$data_dir`, `$port`, `$db_name`, `$db_user`, `$db_pwd`, `$php_version`), and concise comments. YunoHost rejects packages with verbose AI prose, custom directory layouts, or hallucinated helpers.
4. **Never fork `example_ynh`**: Use GitHub's "Use this template" button, start from a fresh git repo, or run the bundled [scaffolder script](./scripts/scaffold_ynh_app.py).

## Step-by-Step Creation Workflow

### Step 1: Analyze Upstream Application
Before writing files, determine:
- **License**: Must be a valid SPDX identifier (FOSS required for official catalog; see [catalog & policy reference](./references/catalog-and-policy.md)).
- **Distribution**: Prebuilt release binary (check `amd64`/`arm64`/`armhf` assets), source tarball, Python wheel/venv, Node.js build, PHP tarball + Composer, Go, or Ruby.
- **Runtime & DB**: Systemd daemon on `127.0.0.1:$port` behind NGINX `proxy_pass`, PHP-FPM socket, or static assets; MariaDB (`mysql`), PostgreSQL (`postgresql`), Redis, or SQLite in `$data_dir`.
- **URL routing**: Supports subpath (`/myapp`) + root (`/`), or root-only (omit `[install.path]` if root-only).
- **Auth**: Supports LDAP (`dc=yunohost,dc=org`), SSOwat HTTP headers (`YNH_USER`, `YNH_USER_EMAIL`, `YNH_USER_FULLNAME`), internal accounts, or no accounts (`ldap = "not_relevant"`, `sso = "not_relevant"`).

### Step 2: Scaffold the Package Structure
Run the bundled zero-dependency Python 3.11+ scaffolder to generate a clean `example_ynh`-compliant skeleton:

```bash
python3 ./scripts/scaffold_ynh_app.py \
  --id myapp \
  --name "My App" \
  --stack proxy \
  --output /path/to/myapp_ynh
```

Supported `--stack` presets: `proxy` (default daemon + systemd + NGINX reverse proxy), `php` (PHP 8.3-FPM + NGINX), `nodejs` (`[resources.nodejs]` + systemd + NGINX), `python` (`python3-venv` + systemd + NGINX), `go` (`[resources.go]` + systemd + NGINX), `static` (static web files + NGINX). Add `--database mysql` or `--database postgresql` when needed.

### Step 3: Complete `manifest.toml` & Resources
Consult [manifest and resources reference](./references/manifest-and-resources.md) for every field and constraint:
- Set real `url` and 64-hex lowercase `sha256` under `[resources.sources.main]` (use `fetch_source_sha256.py` from `yunohost-app-update` to compute hashes directly from URLs) and configure `autoupdate.strategy`.
- Keep `name` <= **22 characters**, `description.en` <= **150 characters** (never include `"for YunoHost"` or start with the app name), and `version` lowercase (`1.0.0~ynh1`).
- Ensure `[resources.apt]` is placed **above** `[resources.database]` and includes `mariadb-server` or `postgresql` when `[resources.database]` is used.

### Step 4: Implement Lifecycle Scripts (`scripts/*`)
Consult [scripts and helpers v2.1 reference](./references/scripts-and-helpers-v2.1.md) for exact signatures of all 96 v2.1 helpers:
- **`install`**: Initialize custom settings -> `ynh_setup_source --dest_dir="$install_dir"` -> build/install app (`ynh_exec_as_app ...`) -> `ynh_config_add` app config (`chmod 400`/`600`, `chown "$app:$app"`) -> `ynh_config_add_nginx` / `ynh_config_add_phpfpm` / `ynh_config_add_systemd` / `yunohost service add` / `ynh_config_add_logrotate` / `ynh_config_add_fail2ban` -> `ynh_systemctl --service="$app" --action="start" --log_path="systemd"` -> `ynh_script_progression "Installation of $app completed"`.
- **`upgrade`**: Stop service -> downward compatibility (`ynh_app_setting_set_default`) -> `ynh_setup_source --dest_dir="$install_dir" --full_replace --keep="..."` -> rebuild/migrate -> update app & system configs (identical `yunohost service add` flags as `install`!) -> start service.
- **`remove`**: Symmetrically remove fail2ban, logrotate, `yunohost service remove "$app"` (guarded by `if ynh_hide_warnings yunohost service status "$app" >/dev/null`), systemd, nginx, phpfpm, and `/etc/$app` (`ynh_safe_rm`). Never delete `$data_dir` or `/var/log/$app` manually.
- **`backup` & `restore`**: Must `source ../settings/scripts/_common.sh` before `source /usr/share/yunohost/helpers`. Declare all app dirs, system configs, and DB dumps in `backup` (using `ynh_print_info`, never `ynh_script_progression`); restore them in `restore`, `systemctl enable "$app.service" --quiet`, re-add `yunohost service add`, and reload `nginx`.
- **`change_url`**: Stop service (if daemon), call `ynh_config_change_url_nginx`, update `$domain`/`$path` in app configs/DB, restart service.

### Step 5: Configure NGINX, Systemd, SSO/LDAP, Docs & Optional Features
- **NGINX, Systemd & Auth**: Consult [NGINX, systemd, SSO & LDAP reference](./references/nginx-systemd-sso-ldap.md) and templates in `./assets/` (`nginx-proxy.conf`, `nginx-php.conf`, `nginx-static.conf`, `systemd.service`). Match `integration.sso = true` with `proxy_params_with_auth;` / `fastcgi_params_with_auth;` and `sso = false` / `"not_relevant"` with `*_params_no_auth;`.
- **Config Panels, Forms, Hooks & Docs**: Consult [config panels, hooks & docs reference](./references/config-panels-hooks-docs.md) and `./assets/config_panel.toml`. Always write meaningful `doc/DESCRIPTION.md` and `doc/ADMIN.md` (remove unused `PRE_*`/`POST_*` dummy files).
- **Tests & Catalog**: Configure `./assets/tests.toml` (`curl_tests` checking expected title/content), validate with `yunohost-app-lint-and-test`, and see [catalog and policy reference](./references/catalog-and-policy.md) to publish in `YunoHost/apps`.

## Reference Library & Bundled Assets

- [Manifest & Resources Reference](./references/manifest-and-resources.md)
- [Scripts & All 96 Helpers v2.1 Reference](./references/scripts-and-helpers-v2.1.md)
- [NGINX, Systemd, PHP-FPM, SSOwat & LDAP Reference](./references/nginx-systemd-sso-ldap.md)
- [Config Panels, Form Types, Hooks & Documentation Reference](./references/config-panels-hooks-docs.md)
- [Catalog Publishing & Policy Reference](./references/catalog-and-policy.md)
- [Package Scaffolder CLI](./scripts/scaffold_ynh_app.py)
- Boilerplate templates: [nginx-proxy.conf](./assets/nginx-proxy.conf), [nginx-php.conf](./assets/nginx-php.conf), [nginx-static.conf](./assets/nginx-static.conf), [systemd.service](./assets/systemd.service), [config_panel.toml](./assets/config_panel.toml), [tests.toml](./assets/tests.toml)
