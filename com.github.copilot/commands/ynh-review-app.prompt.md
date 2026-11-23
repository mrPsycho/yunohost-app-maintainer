---
name: "ynh-review-app"
description: "Audit and lint a YunoHost app package against package_linter rules, security hardening, and Level 7/8 quality criteria"
argument-hint: "<path to *_ynh>"
agent: "yunohost-app-maintainer"
---

Perform a thorough YunoHost package review and quality audit on the target `*_ynh` repository:

1. Load the `yunohost-app-lint-and-test` skill and run its bundled `check_ynh_package.py` static analyzer (plus `package_linter.py` if installed locally).
2. Audit symmetry across `install`, `upgrade`, `remove`, `backup`, `restore`, and `change_url`, checking for helper hallucinations, positional-vs-keyword flag bugs, missing `--keep` paths on upgrade, file permissions, systemd sandboxing, secret exposure, and NGINX SSO/proxy header compliance.
3. Report findings grouped by `package_linter` severity (**Critical**, **Error**, **Warning**, **Info**) and apply fixes if requested.
