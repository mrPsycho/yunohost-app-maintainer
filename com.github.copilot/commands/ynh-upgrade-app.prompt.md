---
name: "ynh-upgrade-app"
description: "Update an existing YunoHost package to a new upstream release or migrate it to Packaging v2 / Helpers v2.1"
argument-hint: "<path to *_ynh> [target upstream version or 'migrate to v2.1']"
agent: "yunohost-app-maintainer"
---

Update or modernize the target YunoHost application package:

1. Load the `yunohost-app-update` skill and inspect the current `manifest.toml` (or `manifest.json`), `scripts/*`, `conf/*`, and `tests.toml`.
2. If upgrading upstream version:
   - Fetch new upstream release tarball/binary URLs and compute exact SHA-256 checksums (`fetch_source_sha256.py`).
   - Update `version` (`<new_ver>~ynh1`, lowercase) in `manifest.toml` and verify `[resources.sources.*.autoupdate]`.
   - Check upstream changelog/breaking changes: update runtime versions (`nodejs`, `php8.3`, `go`, `ruby`), dependencies (`[resources.apt]`), migrations, config templates, downward compatibility (`ynh_app_setting_set_default`, `ynh_app_upgrading_from_version_before`), and add `doc/PRE_UPGRADE.d/<version>.md` or `POST_UPGRADE.d/<version>.md` if admin attention is needed.
3. If migrating Packaging v1 / Helpers v2.0 -> Packaging v2 / Helpers v2.1:
   - Convert declarative provisioning to `[resources.*]`, update `helpers_version = "2.1"` and `yunohost = ">= 12.1.38"`, rename all v2.0 helpers/flags/placeholders to exact v2.1 equivalents, and update NGINX to `proxy_params_*` / `fastcgi_params_*`.
4. Validate with `check_ynh_package.py` from `yunohost-app-lint-and-test` until clean.
