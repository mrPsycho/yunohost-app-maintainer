# YunoHost App Scripts & All 96 Helpers v2.1 Complete Reference

Sources: `doc.yunohost.org/en/dev/packaging/scripts/`, `helpers_v2.1`, `shell_variables_scope`, and `YunoHost/yunohost/tree/dev/helpers/helpers.v2.1.d`.

---

## 1. Script Lifecycle & Variable Scope Rules

### Header & Sourcing Rules
- **In `install`, `upgrade`, `remove`, `change_url`**:
  ```bash
  #!/bin/bash
  source _common.sh
  source /usr/share/yunohost/helpers
  ```
- **In `backup` and `restore`** (cwd `$YNH_CWD` is the backup workdir, NOT `scripts/`!):
  ```bash
  #!/bin/bash
  source ../settings/scripts/_common.sh
  source /usr/share/yunohost/helpers
  ```
- **In `config`** (for `config_panel.toml`):
  ```bash
  #!/bin/bash
  source /usr/share/yunohost/helpers
  ynh_abort_if_errors
  # ... get__*, validate__*, set__*, run__* ...
  ynh_app_config_run "$1"
  ```
- **Error trapping**: `source /usr/share/yunohost/helpers` automatically enables `set -eu` + `trap ynh_exit_properly EXIT` in all scripts except `remove` (which intentionally continues past errors). **NEVER** put `ynh_abort_if_errors` or `set -eu` in `install`, `upgrade`, `remove`, `backup`, `restore`, `change_url`, or `_common.sh` (`package_linter` Error!).

### Variable Scope & Settings Persistence
- Functions called in the same shell share global scope: always use `local var=...` inside functions in `_common.sh` unless mutating a global intentionally.
- Variables set in `install` do **NOT** survive into `upgrade`/`backup`/`restore`/`remove` unless stored in `/etc/yunohost/apps/$app/settings.yml` via `ynh_app_setting_set --key=foo --value="$foo"`.
- Every key in `settings.yml` is automatically loaded as `$<key>` when `source /usr/share/yunohost/helpers` runs.
- Secrets matching `pwd`, `pass`, `passwd`, `password`, `passphrase`, `token`, `secret\w*`, or `\w+key` are automatically redacted in debug logs.

### Keyword (`--flag=val`) vs Positional Argument Enforcement
In Helpers v2.1, `ynh_handle_getopts_args` aborts with `ynh_die` if you pass positional arguments to a **getopts** helper, whereas **positional** helpers treat `--foo=bar` as a literal string! Follow the `[getopts]`, `[positional]`, or `[no-args]` tag on every helper below.

---

## 2. Sources (`sources`)

1. **`ynh_setup_source`** `[getopts]`
   ```bash
   ynh_setup_source --dest_dir="$install_dir" [--source_id="main"] [--keep=".env storage"] [--full_replace]
   ```
   Verifies SHA-256, extracts `[resources.sources.<source_id>]` (or copies/renames if `extract = false`), applies `patches/<source_id>/*.patch` (`patch -p1`), preserves space-separated relative paths in `--keep` (plus `composer.phar` automatically), and applies default ownership if `--dest_dir == $install_dir`. Always pass `--full_replace` in `scripts/upgrade` so obsolete upstream files are cleaned up.

---

## 3. Configurations & Templating (`templating`, `nginx`, `php`, `systemd`, `fail2ban`, `logrotate`)

2. **`ynh_config_add`** `[getopts]`
   ```bash
   ynh_config_add --template="app.env" --destination="$install_dir/.env" [--jinja]
   ```
   Renders `conf/<template>` to `--destination`, backs up manual admin edits if checksum differs, sets default permissions (`600 $app:$app` inside `$install_dir`/`$data_dir`/`/etc/$app`, `400 root:root` elsewhere), and records MD5 checksum in `settings.yml`.
   - Default mode: substitutes uppercase `__FOO_BAR__` with lowercase `$foo_bar` (dies if `$foo_bar` is unset! When `$path == "/"`, `__PATH__/` becomes `/`).
   - `--jinja`: renders Jinja2 (`j2`) with `from_json`, `to_json`, `from_yaml`, `to_yaml`, `from_toml`, `to_toml` filters.
3. **`ynh_read_var_in_file`** `[getopts]`
   ```bash
   val=$(ynh_read_var_in_file --file="$install_dir/config.yml" --key="port" [--after="server:"])
   ```
   Reads scalar value from YAML, JSON, TOML, INI, `.env`, PHP, Python, or JS (returns `YNH_NULL` if absent).
4. **`ynh_write_var_in_file`** `[getopts]`
   ```bash
   ynh_write_var_in_file --file="$install_dir/config.yml" --key="port" --value="$port" [--after="server:"]
   ```
5. **`ynh_config_add_nginx`** `[no-args]`
   Renders `conf/nginx.conf` -> `/etc/nginx/conf.d/$domain.d/$app.conf`, uncomments `#sub_path_only` (when `$path != "/"`) or `#root_path_only` (when `$path == "/"`), stores checksum, and reloads `nginx` (do NOT reload `nginx` again at end of `install`/`upgrade`!).
6. **`ynh_config_remove_nginx`** `[no-args]`
   Removes `/etc/nginx/conf.d/$domain.d/$app.conf` and reloads `nginx`.
7. **`ynh_config_change_url_nginx`** `[no-args]`
   Used in `scripts/change_url`: removes `/etc/nginx/conf.d/$old_domain.d/$app.conf` (backing up manual edits) and calls `ynh_config_add_nginx` for the new `$domain`/`$path`.
8. **`ynh_config_add_phpfpm`** `[no-args]`
   Generates `/etc/php/$php_version/fpm/pool.d/$app.conf` (socket `/var/run/php/php${php_version}-fpm-${app}.sock`), appends `conf/extra_php-fpm.conf` if present, tests config, and reloads `php${php_version}-fpm`. Tunable via settings/variables set beforehand:
   - `$php_upload_max_filesize` (default `50M`, sets `upload_max_filesize` & `post_max_size`)
   - `$php_memory_limit` (default `128M`)
   - `$php_process_management` (`ondemand` default, `dynamic`, `static`)
   - `$php_max_children`, `$php_group` (default `$app`)
9. **`ynh_config_remove_phpfpm`** `[no-args]`
   Removes `/etc/php/$php_version/fpm/pool.d/$app.conf` and reloads `php${php_version}-fpm`.
10. **`ynh_config_add_systemd`** `[getopts]`
    ```bash
    ynh_config_add_systemd [--service="$app"] [--template="systemd.service"] [--mount="..."]
    ```
    Renders `conf/<template>` (default `conf/systemd.service` — **include `.service` extension** on custom template names!) to `/etc/systemd/system/$service.service`, enables it, and runs `systemctl daemon-reload`.
11. **`ynh_config_remove_systemd`** `[positional]`
    ```bash
    ynh_config_remove_systemd ["$service"]   # Defaults to "$app"; NEVER pass --service=!
    ```
12. **`ynh_systemctl`** `[getopts]`
    ```bash
    ynh_systemctl [--service="$app"] [--mount="..."] [--action="start|stop|restart|reload"] [--wait_until="regex"] [--log_path="systemd|/var/log/..."] [--timeout=300] [--length=20]
    ```
    Runs `systemctl`, prints journal/log tail on failure, and optionally waits for extended regex `--wait_until` (never wait on generic `"Started"`/`"Stopped"`).
13. **`ynh_config_add_fail2ban`** `[getopts]`
    ```bash
    ynh_config_add_fail2ban --logpath="/var/log/$app/$app.log" [--failregex="^Failed login from <HOST>$"]
    ```
    Creates `/etc/fail2ban/jail.d/$app.conf` + `/etc/fail2ban/filter.d/$app.conf` (or renders `conf/f2b_jail.conf` + `conf/f2b_filter.conf` if `--failregex` is omitted; always pass `--logpath`!) and reloads `fail2ban`.
14. **`ynh_config_remove_fail2ban`** `[no-args]`
15. **`ynh_config_add_logrotate`** `[positional]`
    ```bash
    ynh_config_add_logrotate ["/var/log/$app/custom.log"]   # Defaults to /var/log/$app/*.log
    ```
16. **`ynh_config_remove_logrotate`** `[no-args]`

---

## 4. Databases (`mysql`, `postgresql`, `mongodb`, `redis`)

*(MariaDB & PostgreSQL DB/user provisioning is automatic via `[resources.database]` -> `$db_name`, `$db_user`, `$db_pwd`.)*

17. **`ynh_mysql_db_shell`** `[positional]`: `ynh_mysql_db_shell ["$db_name"] <<< "SQL;"` or `< ./db.sql`
18. **`ynh_mysql_dump_db`** `[positional]`: `ynh_mysql_dump_db ["$db_name"] > db.sql`
19. **`ynh_psql_db_shell`** `[positional]`: `ynh_psql_db_shell ["$db_name"] <<< "SQL;"` or `< ./db.sql`
20. **`ynh_psql_dump_db`** `[positional]`: `ynh_psql_dump_db ["$db_name"] > db.sql`
21. **`ynh_install_mongo`** `[no-args]`: Set `mongo_version="7.0"` globally first, then call `ynh_install_mongo`.
22. **`ynh_remove_mongo`** `[no-args]`
23. **`ynh_mongo_setup_db`** `[getopts]`: `ynh_mongo_setup_db --db_user="$db_user" --db_name="$db_name" [--db_pwd="$db_pwd"]`
24. **`ynh_mongo_remove_db`** `[getopts]`: `ynh_mongo_remove_db --db_user="$db_user" --db_name="$db_name"`
25. **`ynh_mongo_exec`** `[getopts]`: `ynh_mongo_exec [--database="$db_name"] --command='db.stats()'`
26. **`ynh_mongo_database_exists`** `[getopts]`: `ynh_mongo_database_exists --database="$db_name"`
27. **`ynh_mongo_dump_db`** `[getopts]`: `ynh_mongo_dump_db --database="$db_name" > ./dump.bson`
28. **`ynh_mongo_restore_db`** `[getopts]`: `ynh_mongo_restore_db --database="$db_name" < ./dump.bson`
29. **`ynh_redis_get_free_db`** `[no-args]`: `redis_db=$(ynh_redis_get_free_db)`
30. **`ynh_redis_remove_db`** `[positional]`: `ynh_redis_remove_db "$redis_db"`

---

## 5. Execution, Utils, Settings & Strings (`0-utils`, `setting`, `string`)

31. **`ynh_exec_as_app`** `[positional]`: `ynh_exec_as_app COMMAND [ARG ...]` (runs as `$app` with full `$PATH`, `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`, `NPM_CONFIG_UPDATE_NOTIFIER=false` — pass command **unquoted**!).
32. **`ynh_spawn_app_shell`** `[no-args, stdin]`: `ynh_spawn_app_shell <<< 'php artisan migrate --force'` (runs as `$app` in service `WorkingDirectory` with unit `Environment`/`EnvironmentFile`, `$install_dir/venv`, and `php` alias loaded).
33. **`ynh_local_curl`** `[positional]`: `ynh_local_curl "/install" ["k1=v1" "k2=v2" ...]` (GET if 1 arg, POST if `k=v` args; resolves `$domain:443` to `127.0.0.1` with persistent cookie jar).
34. **`ynh_safe_rm`** `[positional]`: `ynh_safe_rm "/etc/$app"` (**one path per call**, never `--file=`!).
35. **`ynh_read_manifest`** `[positional]`: `ynh_read_manifest "upstream.code"` (jq query on `manifest.toml`).
36. **`ynh_app_upstream_version`** `[no-args]`: Echoes manifest version stripped of `~ynh*`.
37. **`ynh_app_upstream_version_changed`** `[no-args]`: Exit `0` if upstream version changed, `1` if packaging-only `~ynhN` bump.
38. **`ynh_app_upgrading_from_version_before`** `[positional]`: `if ynh_app_upgrading_from_version_before 2.3.0~ynh1; then ...; fi` (`~ynh` suffix mandatory).
39. **`ynh_app_upgrading_from_version_before_or_equal_to`** `[positional]`: `if ynh_app_upgrading_from_version_before_or_equal_to 2.3.0~ynh1; then ...; fi`
40. **`ynh_validate_ip`** `[getopts]`: `ynh_validate_ip --family=4|6 --ip_address="$ip"`
41. **`ynh_in_ci_tests`** `[no-args]`: Exit `0` when running under `package_check`.
42. **`ynh_user_get_info`** `[getopts]`: `ynh_user_get_info --username="$admin" --key=mail|fullname|firstname|lastname|mail-aliases`
43. **`ynh_user_list`** `[no-args]`: Prints all YunoHost usernames, one per line.
44. **`ynh_add_swap`** `[getopts]`: `ynh_add_swap --size=2048` (MB; skipped in containers/SD cards).
45. **`ynh_del_swap`** `[no-args]`
46. **`ynh_smart_mktemp`** `[getopts]`: `tmpdir=$(ynh_smart_mktemp [--min_size=300])`
47. **`ynh_app_setting_get`** `[getopts]`: `ynh_app_setting_get [--app="$app"] --key=foo`
48. **`ynh_app_setting_set`** `[getopts]`: `ynh_app_setting_set [--app="$app"] --key=foo --value="$foo"`
49. **`ynh_app_setting_set_default`** `[getopts]`: `ynh_app_setting_set_default [--app="$app"] --key=foo --value="default"` (sets both `$foo` in current shell and `settings.yml` if unset/empty).
50. **`ynh_app_setting_delete`** `[getopts]`: `ynh_app_setting_delete [--app="$app"] --key=old_foo`
51. **`ynh_string_random`** `[getopts]`: `ynh_string_random [--length=24] [--filter='A-Za-z0-9']`
52. **`ynh_replace`** `[getopts]`: `ynh_replace --match="old" --replace="new" --file="$file"` (call `ynh_store_file_checksum "$file"` afterward if modifying a tracked config!).
53. **`ynh_replace_regex`** `[getopts]`: `ynh_replace_regex --match="TOKEN" --replace="$secret_with_ampersand" --file="$file"` (escapes `\` and `&` safely).
54. **`ynh_normalize_url_path`** `[positional]`: `ynh_normalize_url_path "$subpath"`

---

## 6. Backup, Checksums, Logging, Multimedia & Composer

55. **`ynh_backup`** `[positional]`: `ynh_backup "/path/to/file_or_dir"` (declares one path per call in `scripts/backup`; `$data_dir` and `/var/log/$app` are auto-skipped on `BACKUP_CORE_ONLY=1` pre-upgrade safety backups).
56. **`ynh_restore`** `[positional]`: `ynh_restore "/path/to/file_or_dir"` (restores one path in `scripts/restore`).
57. **`ynh_restore_everything`** `[no-args]`: Restores all app paths in `backup.csv`.
58. **`ynh_store_file_checksum`** `[positional]`: `ynh_store_file_checksum "/path/to/file"`
59. **`ynh_backup_if_checksum_is_different`** `[positional]`: `ynh_backup_if_checksum_is_different "/path/to/file"`
60. **`ynh_delete_file_checksum`** `[positional]`: `ynh_delete_file_checksum "/path/to/file"`
61. **`ynh_die`** `[positional]`: `ynh_die "Fatal error message"` (use instead of `exit`!).
62. **`ynh_print_info`** `[positional]`: `ynh_print_info "Info message"` (use in `scripts/backup` instead of `ynh_script_progression`).
63. **`ynh_print_warn`** `[positional]`: `ynh_print_warn "Warning message"`
64. **`ynh_hide_warnings`** `[positional]`: `ynh_hide_warnings command arg1 arg2` (unquoted command).
65. **`ynh_exec_and_print_stderr_only_if_error`** `[positional]`: `ynh_exec_and_print_stderr_only_if_error command arg1 ...`
66. **`ynh_return`** `[positional]`: `ynh_return "data"` (internal config/hook return channel).
67. **`ynh_script_progression`** `[positional]`: `ynh_script_progression "Setting up source files..."` (**NEVER** pass `--message=`, `--weight=`, `--time`, or `--last`! Include the word `completed` in the final line of `install`/`upgrade`/`remove`/`restore`/`change_url`).
68. **`ynh_multimedia_build_main_dir`** `[no-args]`
69. **`ynh_multimedia_addfolder`** `[getopts]`: `ynh_multimedia_addfolder --source_dir="$data_dir/media" --dest_dir="share/Picture/$app"`
70. **`ynh_multimedia_addaccess`** `[positional]`: `ynh_multimedia_addaccess "$app"`
71–76. **Config Panel Helpers** (`scripts/config`): `ynh_app_config_run "$1"`, `ynh_app_config_get`, `ynh_app_config_show`, `ynh_app_config_validate`, `ynh_app_config_apply`, `ynh_app_action_run "$1"`.
77–96. **Resource-Backed / Dynamic Helpers**:
- Active in scripts when needed dynamically:
  - `ynh_composer_exec` `[positional]`: `ynh_composer_exec install --no-dev --optimize-autoloader` (with `[resources.composer]`)
  - `ynh_permission_url` `[getopts]`, `ynh_permission_update` `[getopts]`, `ynh_permission_exists` `[getopts]`, `ynh_permission_has_user` `[getopts]`, `ynh_permission_delete` `[getopts]`
  - `ynh_system_user_exists --username=...`, `ynh_system_group_exists --group=...`
  - `ynh_get_ram --free|--total`, `ynh_sanitize_dbid --db_name="$app"`
- **Do NOT call directly in v2.1 scripts** (handled by `[resources.*]`): `ynh_apt_install_dependencies`, `ynh_apt_remove_dependencies`, `ynh_apt_install_dependencies_from_extra_repository`, `ynh_system_user_create`, `ynh_system_user_delete`, `ynh_nodejs_install`, `ynh_nodejs_remove`, `ynh_ruby_install`, `ynh_ruby_remove`, `ynh_go_install`, `ynh_go_remove`, `ynh_composer_install`, `ynh_permission_create`.

---

## 7. Python, Rust & Cron Patterns (No Special `ynh_*` Helper Needed)

- **Python (`venv`)**: Add `python3`, `python3-venv`, `python3-pip` (and `build-essential`, `python3-dev` if wheels compile C extensions) to `[resources.apt].packages`, then:
  ```bash
  ynh_exec_as_app python3 -m venv "$install_dir/venv"
  ynh_exec_as_app "$install_dir/venv/bin/pip" install --upgrade pip wheel
  ynh_exec_as_app "$install_dir/venv/bin/pip" install --no-cache-dir -r "$install_dir/requirements.txt"
  ```
- **Cron (`/etc/cron.d/$app`)**: Render `conf/cron` -> `/etc/cron.d/$app` via `ynh_config_add --template="cron" --destination="/etc/cron.d/$app"`, `chown root:root "/etc/cron.d/$app"`, `chmod 644 "/etc/cron.d/$app"`, and include `/etc/cron.d/$app` in `backup`, `restore`, and `remove` (`ynh_safe_rm "/etc/cron.d/$app"`).
