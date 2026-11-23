---
name: "ynh-new-app"
description: "Create a new YunoHost Packaging v2 (Helpers v2.1) application package from an upstream project"
argument-hint: "<app_id or upstream repository URL> [notes on stack/auth]"
agent: "yunohost-app-maintainer"
---

Create a complete, `package_linter`-compliant YunoHost Packaging v2 (`helpers_version = "2.1"`) package for the requested application:

1. Load the `yunohost-app-create` skill and inspect the upstream project (tech stack, release artifacts/tarballs, license SPDX ID, config format, database, subpath support, LDAP/SSO/header-auth support).
2. Scaffold or create `<id>_ynh/` following `YunoHost/example_ynh` structure (`manifest.toml`, `scripts/{_common.sh,install,upgrade,remove,backup,restore,change_url}`, `conf/`, `doc/{DESCRIPTION.md,ADMIN.md}`, `tests.toml`, `.editorconfig`, `LICENSE`, `README.md`).
3. Compute real SHA-256 checksums for `[resources.sources.main]` and configure `[resources.sources.main.autoupdate]` when upstream uses GitHub/GitLab/Gitea/Forgejo tags or releases.
4. Run `check_ynh_package.py` from `yunohost-app-lint-and-test` to verify zero Critical, Error, and Warning issues, and summarize manual test commands (`sudo yunohost app install ... --debug`).
