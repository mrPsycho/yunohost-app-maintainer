---
name: yunohost-app-lint-and-test
description: 'Lint, audit, validate, and test YunoHost application packages (*_ynh) against package_linter rules, manifest.v2.schema.json, tests.toml, package_check CI, Quality Levels 0-8, Incus/ynh-dev, and YunoHost Core architecture (moulinette, yunohost, ssowat, yunohost-admin). Use when reviewing or debugging a YunoHost package, fixing package_linter errors/warnings, writing tests.toml, running package_check, or working on YunoHost core.'
argument-hint: '<path to *_ynh>'
---

# Lint, Test & Debug YunoHost Packages (and Core)

Validate `*_ynh` repositories statically against `package_linter` rules, write `tests.toml` integration tests, run manual or Incus/`package_check` tests, reach App Quality Level 7/8, and understand YunoHost Core internals (`moulinette`, `yunohost`, `ssowat`, `yunohost-admin`, `ynh-dev`).

## When to Use

- Auditing or reviewing any `*_ynh` package before opening a PR or testing on a server
- Fixing `package_linter` Critical, Error, or Warning findings
- Catching hallucinated `ynh_*` helpers, v2.0 -> v2.1 flag mismatches, NGINX security/SSO header issues, or systemd secret leaks
- Writing or debugging `tests.toml` (`curl_tests`, `test_upgrade_from`, multi-suite `only`/`exclude`)
- Running manual `yunohost app install/upgrade` tests, `package_check`, Incus / `ynh-dev`, or VirtualBox test VMs
- Debugging YunoHost Core (`moulinette` actionsmap, `yunohost-api`, `ssowat`, `yunohost-portal`, `yunohost-admin`, translations, docs)

## Step-by-Step Audit & Test Workflow

### Step 1: Run the Bundled Standalone Validator
Run [check_ynh_package.py](./scripts/check_ynh_package.py) (zero external dependencies; requires Python 3.11+ for `tomllib`):

```bash
python3 ./scripts/check_ynh_package.py /path/to/myapp_ynh
```

- Exits with code `1` on any **CRITICAL** or **ERROR** (or with `--strict` on **WARNING** as well—required for Quality Level 7!).
- Validates required files, UTF-8 encoding, `manifest.toml` schema & resource ordering, known vs hallucinated `ynh_*` helpers across all scripts, forbidden bash constructs, script symmetry (`yunohost service add`/`remove`, `backup`/`restore` sourcing), `conf/nginx.conf` rules, and `conf/systemd.service` hardening.
- If the official `YunoHost/package_linter` is also cloned locally, run `./package_linter.py /path/to/myapp_ynh` as a second pass.

### Step 2: Cross-Check Lifecycle Symmetry Manually
Even when static checks pass, verify these semantic invariants:
1. **`upgrade` `--keep` completeness**: Does `ynh_setup_source --dest_dir="$install_dir" --full_replace --keep="..."` preserve every rendered config file (`.env`, `config.json`, `local.php`) or runtime folder stored inside `$install_dir`?
2. **Backup/Restore completeness**: Is every path created outside `[resources.*]` (`/etc/nginx/conf.d/$domain.d/$app.conf`, `/etc/systemd/system/$app.service`, `/etc/php/$php_version/fpm/pool.d/$app.conf`, `/etc/logrotate.d/$app`, `/etc/fail2ban/{jail,filter}.d/$app.conf`, `/etc/cron.d/$app`, `/var/log/$app/`, plus `$install_dir`, `$data_dir`, and SQL dumps) present in **both** `scripts/backup` and `scripts/restore`?
3. **Subpath & multi-instance safety**: Are all paths, systemd service names, sockets, and log directories parameterized with `$app` / `__APP__` and `$path` / `__PATH__` rather than hardcoded to the app's base ID or `/`?

### Step 3: Configure `tests.toml` & Test Locally / in CI
Consult [testing, CI, and core development reference](./references/testing-ci-and-core-dev.md):
- Add meaningful `[default.curl_tests]` assertions (`expect_title`, `expect_content`, `expect_return_code`) so `package_check` verifies the app actually renders rather than serving an error page with HTTP 200.
- Test manually on a disposable YunoHost VM or Incus container:
  ```bash
  sudo yunohost app install ./myapp_ynh --debug --no-remove-on-failure --force \
    -a "domain=test.domain.tld&path=/myapp&init_main_permission=visitors"
  sudo yunohost backup create --apps myapp --debug
  sudo yunohost app upgrade myapp -f ./myapp_ynh --debug
  sudo yunohost app change-url myapp -d test.domain.tld -p /moved --debug
  sudo yunohost app remove myapp --purge --debug
  sudo yunohost backup restore <archive_name> --apps myapp --debug
  ```
- Or run full automated container CI locally with `./package_check.sh /path/to/myapp_ynh`.

## References & Scripts

- [Complete `package_linter` Rules & Anti-Patterns](./references/package-linter-rules.md)
- [Testing (`tests.toml`, `package_check`, Quality Levels 0–8), Incus/`ynh-dev` & Core Architecture](./references/testing-ci-and-core-dev.md)
- [Standalone Package Linter & Helper Validator](./scripts/check_ynh_package.py)
