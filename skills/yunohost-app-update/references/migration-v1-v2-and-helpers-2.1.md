# Packaging v1 -> v2 & Helpers v2.0 -> v2.1 Complete Migration Reference

Sources: `doc.yunohost.org/en/dev/packaging/advanced/packaging_v2`, `scripts/helpers_v2.0`, `scripts/helpers_v2.1`, and `YunoHost/yunohost/helpers/helpers.v2.1.d`.

---

## 1. Packaging v1 (`manifest.json`) -> Packaging v2 (`manifest.toml`)

*(Official helper tool if migrating a large v1 repo: `YunoHost/apps_tools/packaging_v2/convert_app_to_packaging_v2.py` — always review output manually and upgrade to `helpers_version = "2.1"` afterward!)*

| Area | Packaging v1 (`manifest.json`) | Packaging v2 (`manifest.toml`) |
|---|---|---|
| Manifest & Sources | `manifest.json` + `conf/*.src` | Single `manifest.toml` (`[resources.sources.<id>]` with `url`, `sha256`, `autoupdate`) |
| Install args | Read `$YNH_APP_ARG_*` + manual `ynh_app_setting_set` | Auto-saved in `settings.yml` & auto-loaded as `$<key>` (except `password` and `init_*_permission`) |
| Loading settings | Manual `foo=$(ynh_app_setting_get ...)` in every script | Auto-loaded into global bash variables upon `source /usr/share/yunohost/helpers` |
| Error trapping | Manual `ynh_abort_if_errors` in every script | Auto-enabled by core (**error** in `package_linter` if kept in `install`/`upgrade`/`remove`/`backup`/`restore`!) |
| Pre-upgrade backup | Manual `ynh_backup_before_upgrade` + `ynh_clean_setup` | Handled automatically by YunoHost core before `scripts/upgrade` |
| Public/private | `is_public` boolean + manual `ynh_permission_update` | `[install.init_main_permission]` (`type = "group"`, `default = "visitors"` or `"all_users"`) + `[resources.permissions] main.url = "/"` |
| System resources | Manual user/dir/port/apt/DB/Node/Ruby/Go helpers in `install`/`upgrade`/`restore`/`remove` | Declarative `[resources.*]` (`system_user`, `install_dir`, `data_dir`, `ports`, `apt`, `database`, `nodejs`, `ruby`, `go`, `composer`) |
| Admin emails | `ynh_send_readme_to_admin` | `doc/ADMIN.md`, `doc/POST_INSTALL.md`, `doc/PRE_UPGRADE.d/<ver>.md`, `doc/POST_UPGRADE.md` |

### Variable & Placeholder Renames (Core Auto-Migrates Settings on Upgrade!)
- `$final_path` / `__FINALPATH__` -> `$install_dir` / `__INSTALL_DIR__` (and moves `/opt/yunohost/$app` -> `/var/www/$app` automatically!)
- `$datadir` / `__DATADIR__` -> `$data_dir` / `__DATA_DIR__`
- `$path_url` -> `$path` (`__PATH__`)
- `$mysqlpwd` / `$mysqldbpwd` / `$psqlpwd` -> `$db_pwd` (`__DB_PWD__`)
- `$<name>_port` / `__<NAME>_PORT__` -> `$port_<name>` / `__PORT_<NAME>__` (`main` port is `$port` / `__PORT__`)
- `$phpversion` / `__PHPVERSION__` -> `$php_version` / `__PHP_VERSION__` (auto-migrated when v2.1 `setting` helper loads!)

---

## 2. Helpers v2.0 -> Helpers v2.1 Complete Rename & Signature Matrix

Set `yunohost = ">= 12.1.38"` (or `">= 12.1.17"`) and `helpers_version = "2.1"` under `[integration]` in `manifest.toml`, then apply **every** rename below:

| Helpers v2.0 (`helpers_version = "2.0"` or omitted) | Helpers v2.1 (`helpers_version = "2.1"`) | Breaking Argument / Behavior Change |
|---|---|---|
| `ynh_add_config --template=T --destination=D [--jinja]` | `ynh_config_add --template=T --destination=D [--jinja]` | Legacy magic tokens (`__FINALPATH__`, `__NAME__`, `__USER__`) removed; strictly `__FOO__` -> `$foo` |
| `ynh_add_nginx_config` | `ynh_config_add_nginx` | Uses `$path` instead of `$path_url` |
| `ynh_remove_nginx_config` | `ynh_config_remove_nginx` | — |
| `ynh_change_url_nginx_config` | `ynh_config_change_url_nginx` | — |
| `ynh_add_fpm_config [--usage=... --footprint=...]` | `ynh_config_add_phpfpm` | No CLI flags! Configure via `$php_upload_max_filesize`, `$php_memory_limit`, `$php_process_management`, `$php_max_children`, `$php_group` + optional `conf/extra_php-fpm.conf` |
| `ynh_remove_fpm_config` | `ynh_config_remove_phpfpm` | — |
| `ynh_add_systemd_config [--service=S] [--template=systemd]` | `ynh_config_add_systemd [--service=S] [--template=systemd.service] [--mount=M]` | Default template is now `conf/systemd.service` (**must include `.service` extension**!) |
| `ynh_remove_systemd_config [--service=S]` | `ynh_config_remove_systemd [S]` | Changed from `--service=` to **positional** `[S]`! |
| `ynh_systemd_action --service_name=S --action=A --line_match=M` | `ynh_systemctl --service=S --action=A --wait_until=M [--log_path=systemd]` | `--service_name` -> `--service`; `--line_match` -> `--wait_until` |
| `ynh_add_fail2ban_config --logpath=L --failregex=R [--max_retry=...] [--ports=...]` | `ynh_config_add_fail2ban --logpath=L [--failregex=R]` | `--max_retry`, `--ports`, `--use_template` **removed** (uses `conf/f2b_jail.conf` + `conf/f2b_filter.conf` when `--failregex` omitted) |
| `ynh_remove_fail2ban_config` | `ynh_config_remove_fail2ban` | — |
| `ynh_use_logrotate [--logfile=P] [--specific_user=...]` | `ynh_config_add_logrotate [P]` | Changed from `--logfile=` to **positional** `[P]`! |
| `ynh_remove_logrotate` | `ynh_config_remove_logrotate` | — |
| `sources/patches/<id>-*.patch` + `sources/extra_files/<id>` | `patches/<id>/*.patch` | Patch folder moved to top-level `patches/<id>/`! `sources/extra_files` **removed**! |
| `ynh_mysql_connect_as` / `ynh_mysql_execute_as_root` / `ynh_mysql_execute_file_as_root` | `ynh_mysql_db_shell [db] <<< "SQL"` or `< file.sql` | Positional `[db]` (defaults to `$db_name`) |
| `ynh_mysql_dump_db [--database=db]` | `ynh_mysql_dump_db [db] > db.sql` | Positional `[db]` (**do NOT pass `--database=`**!) |
| `ynh_psql_connect_as` / `ynh_psql_execute_as_root` / `ynh_psql_execute_file_as_root` | `ynh_psql_db_shell [db] <<< "SQL"` or `< file.sql` | Positional `[db]` (defaults to `$db_name`) |
| `ynh_psql_dump_db [--database=db]` | `ynh_psql_dump_db [db] > db.sql` | Positional `[db]` (**do NOT pass `--database=`**!) |
| `ynh_replace_string --match_string=M --replace_string=R --target_file=F` | `ynh_replace --match=M --replace=R --file=F` | Function AND all 3 flags shortened! |
| `ynh_replace_special_string --match_string=M --replace_string=R --target_file=F` | `ynh_replace_regex --match=M --replace=R --file=F` | Escapes `\` and `&` before calling `ynh_replace` |
| `ynh_secure_remove --file=P` | `ynh_safe_rm P` | Single **positional** path (**do NOT pass `--file=`**!) |
| `ynh_backup --src_path=P [--dest_path=...] [--is_big] [--not_mandatory]` | `ynh_backup P` | Single **positional** path (**all `--*` flags removed**!) |
| `ynh_restore` *(restored all)* | `ynh_restore_everything` *(restores all)* | **CRITICAL INVERSION**: `ynh_restore` in v2.1 takes a path and restores ONE item! |
| `ynh_restore_file --origin_path=P [--not_mandatory]` | `ynh_restore P` | Single **positional** path! |
| `ynh_store_file_checksum --file=P` | `ynh_store_file_checksum P` | Positional `P` |
| `ynh_backup_if_checksum_is_different --file=P` | `ynh_backup_if_checksum_is_different P` | Positional `P` |
| `ynh_delete_file_checksum --file=P` | `ynh_delete_file_checksum P` | Positional `P` |
| `ynh_script_progression --message="M" [--weight=...] [--time] [--last]` | `ynh_script_progression "M"` | Single **positional** string (**all `--*` flags removed**!) |
| `ynh_die --message="M" [--ret_code=...]` | `ynh_die "M"` | Single **positional** string |
| `ynh_print_info --message="M"` / `ynh_print_warn --message="M"` | `ynh_print_info "M"` / `ynh_print_warn "M"` | Single **positional** string |
| `ynh_exec_warn_less cmd ...` | `ynh_hide_warnings cmd ...` | Renamed (`ynh_exec_quiet` / `ynh_exec_fully_quiet` / `ynh_print_err` removed) |
| `ynh_exec_as $app cmd ...` | `ynh_exec_as_app cmd ...` | Runs as `$app` automatically (**no username arg**!) |
| `ynh_composer_exec --commands="install --no-dev"` | `ynh_composer_exec install --no-dev` | Pass composer args directly as **positional** arguments! |
| `ynh_install_nodejs` / `ynh_use_nodejs` / `ynh_npm` / `$ynh_node_load_PATH` | `[resources.nodejs]` + `ynh_exec_as_app npm ...` + `__NODEJS_DIR__` / `__PATH_WITH_NODEJS__` | `ynh_use_*` and `ynh_npm`/`ynh_node`/`ynh_gem` aliases **removed** (`$PATH` is auto-configured on helper load!) |
| `ynh_compare_current_package_version --comparison lt --version V` | `ynh_app_upgrading_from_version_before V` | Positional `V` (must include `~ynhN`) |
| `ynh_check_app_version_changed` | `ynh_app_upstream_version_changed` | Returns exit code `0`/`1` instead of echoing string |
| `ynh_read_manifest --manifest_key=K` | `ynh_read_manifest "K"` | Positional jq key |
| `ynh_multimedia_addaccess --user_name=U` | `ynh_multimedia_addaccess U` | Positional `U` |

---

## 3. Top Hallucination Traps to Catch During Review

1. **Fake helpers that DO NOT EXIST**: `ynh_python_install`, `ynh_pip_install`, `ynh_rust_install`, `ynh_cargo_build`, `ynh_java_install`, `ynh_config_add_cron`, `ynh_add_cron_config`, `ynh_create_dir`, `ynh_download_source`.
2. **Mixing v2.0 `--flags` into v2.1 positional helpers**: e.g. `ynh_script_progression --message="Installing..."` literally outputs `> --message=Installing...`!
3. **Confusing v2.0 `ynh_restore` (all) with v2.1 `ynh_restore "$path"` (single)**: Calling `ynh_restore` with zero args in v2.1 fails! Use `ynh_restore "$path"` per item or `ynh_restore_everything`.
4. **Multiple paths in `ynh_safe_rm` or `ynh_backup`**: Both ignore 2nd+ arguments — call once per path!
