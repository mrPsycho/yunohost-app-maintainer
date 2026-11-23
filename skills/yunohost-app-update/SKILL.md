---
name: yunohost-app-update
description: 'Update existing YunoHost application packages (*_ynh) to new upstream releases, bump ~ynhN revisions, compute source SHA-256 checksums, configure autoupdate strategies, write downward-compatible upgrade scripts and PRE_UPGRADE.d/POST_UPGRADE.d notices, use YunoHost-Apps PR bots (!testme, !bump), or migrate legacy Packaging v1 and Helpers v2.0 packages to Packaging v2 and Helpers v2.1.'
argument-hint: '<path to *_ynh> [new version, release URL, or "migrate to v2.1"]'
---

# Update & Migrate YunoHost Application Packages

Safely upgrade existing `*_ynh` packages to new upstream releases, configure automated source updates, maintain backward compatibility for installed YunoHost servers, or modernize legacy v1 / Helpers v2.0 apps to Packaging v2 + Helpers v2.1.

## When to Use

- Bumping an existing `*_ynh` package to a newer upstream release or packaging fix (`~ynhN`)
- Computing SHA-256 hashes for single-arch or multi-arch (`amd64`, `arm64`, `armhf`, `i386`) upstream assets
- Configuring `[resources.sources.<id>.autoupdate]` (`latest_github_release`, `latest_gitlab_tag`, etc.)
- Writing safe `scripts/upgrade` migrations (`ynh_app_setting_set_default`, `ynh_app_upgrading_from_version_before`, `--full_replace --keep=...`)
- Adding version-gated admin notices (`doc/PRE_UPGRADE.d/<version>.md` / `POST_UPGRADE.d/<version>.md`)
- Migrating a legacy Packaging v1 (`manifest.json` + `conf/*.src`) or Helpers v2.0 package to Packaging v2 + Helpers v2.1
- Working with `YunoHost-Apps` branches (`testing`, `main`, `ci-auto-update-*`) and PR bot commands (`!testme`, `!bump`, `!changelog`)

## Workflow A: Upgrade an App to a New Upstream Version

### Step 1: Inspect Current Package & Upstream Release Notes
1. Read `manifest.toml`, `scripts/install`, `scripts/upgrade`, `conf/*`, and `tests.toml`.
2. Check upstream release notes / commits between the old version and target version for:
   - New or bumped runtime requirements (`nodejs`, `php8.3-*`, `go`, `ruby`, `python3`, `apt` libraries)
   - New or renamed `.env` / config keys or removed deprecated config options
   - Database migrations or CLI upgrade commands (e.g. `php artisan migrate --force`, `npm run migrate`)
   - Changed release asset naming or archive directory nesting (`in_subdir`)

### Step 2: Update `version` & `[resources.sources.*]` Checksums
- Set `version = "<new_upstream_version>~ynh1"` (**strictly lowercase** `0-9a-z`, e.g. `2.4.0~ynh1`).
  - If upstream version did **not** change (packaging-only fix), increment `~ynhN` -> `~ynh(N+1)`.
- Compute exact SHA-256 checksums using the bundled [SHA-256 fetcher script](./scripts/fetch_source_sha256.py):
  ```bash
  # Single URL:
  python3 ./scripts/fetch_source_sha256.py \
    --url "https://github.com/org/app/archive/refs/tags/v2.4.0.tar.gz"

  # Multi-architecture release binaries:
  python3 ./scripts/fetch_source_sha256.py \
    --arch amd64="https://github.com/org/app/releases/download/v2.4.0/app-linux-amd64.tar.gz" \
    --arch arm64="https://github.com/org/app/releases/download/v2.4.0/app-linux-arm64.tar.gz"
  ```
- Verify or add `[resources.sources.main.autoupdate]` (see [autoupdate & CI bots reference](./references/autoupdate-and-ci-bots.md)).

### Step 3: Ensure Downward Compatibility in `scripts/upgrade`
Installed YunoHost instances upgrading from older package revisions only have the settings that existed when they installed!
1. Initialize any newly introduced setting in **both** `scripts/install` AND `scripts/upgrade`:
   ```bash
   ynh_app_setting_set_default --key=jwt_secret --value="$(ynh_string_random --length=32)"
   ```
2. Gate one-off data/config migrations using `ynh_app_upgrading_from_version_before` (must include `~ynh`!):
   ```bash
   if ynh_app_upgrading_from_version_before 2.4.0~ynh1; then
       ynh_app_setting_delete --key=obsolete_flag
   fi
   ```
3. Ensure `ynh_setup_source --dest_dir="$install_dir" --full_replace --keep="..."` lists **every** config file, `.env`, plugin dir, or local state stored inside `$install_dir` (paths relative to `$install_dir`, no leading `$install_dir/` or trailing `/`).
4. Keep the `SYSTEM CONFIGURATION` section (`ynh_config_add_nginx`, `ynh_config_add_systemd`, `yunohost service add ...`, etc.) **identical** between `scripts/install` and `scripts/upgrade`.
5. If breaking changes require admin action or awareness, create `doc/PRE_UPGRADE.d/<new_version>.md` or `doc/POST_UPGRADE.d/<new_version>.md`.
6. Update `test_upgrade_from.<commit_sha>` in `tests.toml` if appropriate so `package_check` tests real upgrades from the previous `main` commit.

## Workflow B: Migrate Packaging v1 / Helpers v2.0 -> Packaging v2 & Helpers v2.1

Consult the complete [v1/v2.0 -> v2.1 migration & anti-hallucination matrix](./references/migration-v1-v2-and-helpers-2.1.md):
1. If still on `manifest.json` (v1): move metadata, install questions, and `conf/*.src` into `manifest.toml` (`packaging_format = 2`) and delete `manifest.json` + `conf/*.src`.
2. Set `yunohost = ">= 12.1.38"` and `helpers_version = "2.1"` under `[integration]`.
3. Move imperative provisioning (`ynh_install_app_dependencies`, `ynh_mysql_setup_db`, `ynh_system_user_create`, `ynh_find_port`, `ynh_nodejs_install`, etc.) into declarative `[resources.*]` blocks.
4. Remove `ynh_abort_if_errors`, `ynh_clean_setup`, `ynh_backup_before_upgrade`, and manual `ynh_app_setting_get` boilerplate from lifecycle scripts.
5. Rename all v2.0 helpers, flags, and placeholders (`$final_path` -> `$install_dir`, `$phpversion` -> `$php_version`, `ynh_add_nginx_config` -> `ynh_config_add_nginx`, `ynh_restore` -> `ynh_restore_everything` / `ynh_restore_file --origin_path=` -> `ynh_restore`, `ynh_script_progression --message=` -> `ynh_script_progression "..."`, etc.).
6. Update `conf/nginx.conf` to use `include proxy_params_no_auth;` / `proxy_params_with_auth;` or `fastcgi_params_*`.
7. Validate with `yunohost-app-lint-and-test` (`check_ynh_package.py`).

## References & Scripts

- [Migration Matrix (v1 -> v2 & Helpers v2.0 -> v2.1) & Hallucination Traps](./references/migration-v1-v2-and-helpers-2.1.md)
- [Autoupdate Strategies, Branch Workflow & CI Bot Commands](./references/autoupdate-and-ci-bots.md)
- [Upstream Source SHA-256 Fetcher Script](./scripts/fetch_source_sha256.py)
