#!/usr/bin/env python3
"""Standalone zero-dependency static linter for YunoHost Packaging v2 (Helpers v2.1) apps."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REQUIRED_TOP_KEYS = {
    "packaging_format",
    "id",
    "name",
    "description",
    "version",
    "maintainers",
    "upstream",
    "integration",
    "install",
    "resources",
}

ALLOWED_TOP_KEYS = REQUIRED_TOP_KEYS | {"antifeatures"}

CORE_QUESTIONS_NO_ASK = {
    ("domain", "domain"),
    ("path", "path"),
    ("admin", "user"),
    ("is_public", "boolean"),
    ("password", "password"),
    ("init_main_permission", "group"),
}

VALID_QUESTION_TYPES = {
    "string", "text", "select", "tags", "email", "url", "date", "time",
    "color", "password", "path", "boolean", "domain", "user", "group",
    "number", "range", "alert", "markdown", "file", "app",
}

VALID_SOURCE_FORMATS = {
    "tar.bz2", "tar.gz", "tar.xz", "tar.zst", "xz", "zip", "zst", "docker", "whatever",
}

VALID_RESOURCE_KEYS = {
    "sources", "system_user", "install_dir", "data_dir", "permissions",
    "ports", "apt", "database", "nodejs", "ruby", "go", "composer",
}

# Complete whitelist of real YunoHost v2.1 helpers
KNOWN_V21_HELPERS = {
    "ynh_setup_source",
    "ynh_mysql_db_shell", "ynh_mysql_dump_db",
    "ynh_psql_db_shell", "ynh_psql_dump_db",
    "ynh_mongo_exec", "ynh_mongo_dump_db", "ynh_mongo_database_exists",
    "ynh_mongo_restore_db", "ynh_mongo_setup_db", "ynh_mongo_remove_db",
    "ynh_install_mongo", "ynh_remove_mongo",
    "ynh_redis_get_free_db", "ynh_redis_remove_db",
    "ynh_config_add", "ynh_read_var_in_file", "ynh_write_var_in_file",
    "ynh_config_add_nginx", "ynh_config_remove_nginx", "ynh_config_change_url_nginx",
    "ynh_config_add_phpfpm", "ynh_config_remove_phpfpm",
    "ynh_config_add_systemd", "ynh_config_remove_systemd", "ynh_systemctl",
    "ynh_config_add_fail2ban", "ynh_config_remove_fail2ban",
    "ynh_config_add_logrotate", "ynh_config_remove_logrotate",
    "ynh_exec_as_app", "ynh_local_curl", "ynh_safe_rm", "ynh_read_manifest",
    "ynh_app_upstream_version", "ynh_app_upstream_version_changed",
    "ynh_app_upgrading_from_version_before",
    "ynh_app_upgrading_from_version_before_or_equal_to",
    "ynh_validate_ip", "ynh_in_ci_tests", "ynh_user_get_info", "ynh_user_list",
    "ynh_spawn_app_shell", "ynh_add_swap", "ynh_del_swap", "ynh_smart_mktemp",
    "ynh_get_ram", "ynh_sanitize_dbid", "ynh_abort_if_errors", "ynh_exit_properly",
    "ynh_app_setting_get", "ynh_app_setting_set",
    "ynh_app_setting_set_default", "ynh_app_setting_delete",
    "ynh_string_random", "ynh_replace", "ynh_replace_regex", "ynh_normalize_url_path",
    "ynh_backup", "ynh_restore", "ynh_restore_everything",
    "ynh_store_file_checksum", "ynh_backup_if_checksum_is_different", "ynh_delete_file_checksum",
    "ynh_die", "ynh_print_info", "ynh_print_warn", "ynh_hide_warnings",
    "ynh_exec_and_print_stderr_only_if_error", "ynh_return", "ynh_script_progression",
    "ynh_multimedia_build_main_dir", "ynh_multimedia_addfolder", "ynh_multimedia_addaccess",
    "ynh_app_config_run", "ynh_app_config_get", "ynh_app_config_get_one",
    "ynh_app_config_show", "ynh_app_config_validate", "ynh_app_config_apply",
    "ynh_app_config_apply_one", "ynh_app_action_run",
    "ynh_permission_delete", "ynh_permission_exists", "ynh_permission_url",
    "ynh_permission_update", "ynh_permission_has_user",
    "ynh_system_user_exists", "ynh_system_group_exists",
    "ynh_composer_exec",
}

RESOURCE_DEPRECATED_HELPERS = {
    "ynh_apt_install_dependencies": "Use [resources.apt] in manifest.toml",
    "ynh_apt_remove_dependencies": "Use [resources.apt] in manifest.toml",
    "ynh_apt_install_dependencies_from_extra_repository": "Use [resources.apt.extras.<name>] in manifest.toml",
    "ynh_install_app_dependencies": "Deprecated v2.0 helper; use [resources.apt] in manifest.toml",
    "ynh_remove_app_dependencies": "Deprecated v2.0 helper; use [resources.apt] in manifest.toml",
    "ynh_system_user_create": "Use [resources.system_user] in manifest.toml",
    "ynh_system_user_delete": "Use [resources.system_user] in manifest.toml",
    "ynh_nodejs_install": "Use [resources.nodejs] in manifest.toml",
    "ynh_nodejs_remove": "Use [resources.nodejs] in manifest.toml",
    "ynh_ruby_install": "Use [resources.ruby] in manifest.toml",
    "ynh_ruby_remove": "Use [resources.ruby] in manifest.toml",
    "ynh_go_install": "Use [resources.go] in manifest.toml",
    "ynh_go_remove": "Use [resources.go] in manifest.toml",
    "ynh_composer_install": "Use [resources.composer] in manifest.toml",
    "ynh_composer_remove": "Use [resources.composer] in manifest.toml",
    "ynh_permission_create": "Use [resources.permissions] in manifest.toml",
}

V20_RENAMED_HELPERS = {
    "ynh_add_config": "ynh_config_add",
    "ynh_add_nginx_config": "ynh_config_add_nginx",
    "ynh_remove_nginx_config": "ynh_config_remove_nginx",
    "ynh_change_url_nginx_config": "ynh_config_change_url_nginx",
    "ynh_add_fpm_config": "ynh_config_add_phpfpm",
    "ynh_remove_fpm_config": "ynh_config_remove_phpfpm",
    "ynh_add_systemd_config": "ynh_config_add_systemd",
    "ynh_remove_systemd_config": "ynh_config_remove_systemd",
    "ynh_systemd_action": "ynh_systemctl",
    "ynh_add_fail2ban_config": "ynh_config_add_fail2ban",
    "ynh_remove_fail2ban_config": "ynh_config_remove_fail2ban",
    "ynh_use_logrotate": "ynh_config_add_logrotate",
    "ynh_remove_logrotate": "ynh_config_remove_logrotate",
    "ynh_secure_remove": "ynh_safe_rm",
    "ynh_replace_string": "ynh_replace",
    "ynh_replace_special_string": "ynh_replace_regex",
    "ynh_restore_file": "ynh_restore",
    "ynh_exec_warn_less": "ynh_hide_warnings",
    "ynh_exec_as": "ynh_exec_as_app",
    "ynh_mysql_connect_as": "ynh_mysql_db_shell",
    "ynh_mysql_execute_as_root": "ynh_mysql_db_shell",
    "ynh_mysql_execute_file_as_root": "ynh_mysql_db_shell",
    "ynh_psql_connect_as": "ynh_psql_db_shell",
    "ynh_psql_execute_as_root": "ynh_psql_db_shell",
    "ynh_psql_execute_file_as_root": "ynh_psql_db_shell",
}

POSITIONAL_V21_HELPERS_NO_FLAGS = {
    "ynh_script_progression",
    "ynh_die",
    "ynh_print_info",
    "ynh_print_warn",
    "ynh_safe_rm",
    "ynh_backup",
    "ynh_restore",
    "ynh_config_remove_systemd",
    "ynh_config_add_logrotate",
    "ynh_mysql_dump_db",
    "ynh_psql_dump_db",
    "ynh_store_file_checksum",
    "ynh_backup_if_checksum_is_different",
    "ynh_delete_file_checksum",
}


@dataclass
class Finding:
    severity: str  # CRITICAL, ERROR, WARNING, INFO
    location: str
    message: str


class PackageAuditor:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[Finding] = []
        self.manifest: dict = {}

    def add(self, severity: str, location: str, message: str) -> None:
        self.findings.append(Finding(severity, location, message))

    def run(self) -> list[Finding]:
        self.check_files_and_encoding()
        self.check_manifest()
        self.check_scripts()
        self.check_configs()
        return self.findings

    def check_files_and_encoding(self) -> None:
        mandatory = [
            "LICENSE",
            "README.md",
            "manifest.toml",
            "tests.toml",
            "doc/DESCRIPTION.md",
            "scripts/install",
            "scripts/remove",
            "scripts/upgrade",
            "scripts/backup",
            "scripts/restore",
        ]
        for rel in mandatory:
            p = self.root / rel
            if not p.is_file() or p.stat().st_size == 0:
                self.add("ERROR", rel, f"Missing or empty mandatory file '{rel}'.")

        if (self.root / "manifest.json").exists():
            self.add("ERROR", "manifest.json", "Legacy Packaging v1 manifest.json present; migrate to manifest.toml.")
        if (self.root / "config_panel.toml.example").exists():
            self.add("WARNING", "config_panel.toml.example", "Remove leftover config_panel.toml.example.")
        if (self.root / "doc/DISCLAIMER.md").exists():
            self.add("WARNING", "doc/DISCLAIMER.md", "doc/DISCLAIMER.md is obsolete in Packaging v2.")
        if (self.root / "doc/screenshots/example.jpg").exists():
            self.add("WARNING", "doc/screenshots/example.jpg", "Remove dummy doc/screenshots/example.jpg.")
        if (self.root / "scripts/config").exists() and not (self.root / "config_panel.toml").exists():
            self.add("WARNING", "scripts/config", "scripts/config exists without config_panel.toml.")

        lic = self.root / "LICENSE"
        if lic.is_file() and "File containing the license of your package" in lic.read_text(errors="ignore"):
            self.add("ERROR", "LICENSE", "LICENSE still contains template placeholder text.")

        for p in self.root.rglob("*"):
            if ".git" in p.parts or not p.is_file():
                continue
            rel = str(p.relative_to(self.root))
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".gz", ".xz", ".zip"}:
                if p.parent.name == "screenshots" and p.stat().st_size > 1024 * 1024:
                    self.add("WARNING", rel, "Screenshot exceeds 1024 KB.")
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self.add("ERROR", rel, "File is not valid UTF-8.")
                continue
            if "REPLACEBYYOURAPP" in text:
                self.add("ERROR", rel, "Contains leftover REPLACEBYYOURAPP placeholder.")
            if rel.startswith("doc/"):
                if "This is a dummy" in text or "Ceci est une fausse" in text or "lorem ipsum" in text.lower():
                    self.add("WARNING", rel, "Contains dummy/placeholder documentation text.")
                if "__DB_PWD__" in text:
                    self.add("WARNING", rel, "Do not expose __DB_PWD__ in doc/; automate DB config in install script.")

    def check_manifest(self) -> None:
        mpath = self.root / "manifest.toml"
        if not mpath.is_file():
            return
        raw = mpath.read_text(encoding="utf-8", errors="replace")
        try:
            data = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            self.add("CRITICAL", "manifest.toml", f"Invalid TOML syntax: {exc}")
            return
        self.manifest = data

        if "FIXME" in raw:
            self.add("WARNING", "manifest.toml", "Contains unresolved FIXME comment(s).")

        missing = REQUIRED_TOP_KEYS - set(data.keys())
        if missing:
            self.add("CRITICAL", "manifest.toml", f"Missing required top-level keys: {sorted(missing)}")
        unknown = set(data.keys()) - ALLOWED_TOP_KEYS
        if unknown:
            self.add("ERROR", "manifest.toml", f"Unknown top-level keys not allowed by schema: {sorted(unknown)}")

        if data.get("packaging_format") != 2:
            self.add("ERROR", "manifest.toml", "packaging_format must be 2.")

        app_id = data.get("id", "")
        if not isinstance(app_id, str) or not re.match(r"^[a-z0-9]((_|-)?[a-z0-9])+$", app_id):
            self.add("ERROR", "manifest.toml", f"Invalid id '{app_id}'.")
        elif app_id.endswith("_ynh"):
            self.add("WARNING", "manifest.toml", "id should not end with '_ynh'.")

        name = data.get("name", "")
        if isinstance(name, str) and len(name) > 22:
            self.add("ERROR", "manifest.toml", f"name '{name}' is {len(name)} chars (max 22 allowed by package_linter).")

        desc = data.get("description")
        desc_en = desc.get("en", "") if isinstance(desc, dict) else (desc if isinstance(desc, str) else "")
        if "for yunohost" in desc_en.lower():
            self.add("ERROR", "manifest.toml", "description must not contain 'for YunoHost'.")
        if not (5 <= len(desc_en) <= 150):
            self.add("WARNING", "manifest.toml", f"description.en length ({len(desc_en)}) should be between 5 and 150 chars.")
        if app_id and desc_en.lower().startswith((app_id.lower(), str(name).lower())):
            self.add("WARNING", "manifest.toml", "description should explain what the app does without starting with its name.")

        version = data.get("version", "")
        if not isinstance(version, str) or not re.match(r"^[0-9a-z]*([.+-][0-9a-z]*)*~ynh[0-9]+$", version):
            self.add("ERROR", "manifest.toml", f"Invalid version '{version}': must be lowercase '<upstream>~ynh<N>'.")

        maintainers = data.get("maintainers")
        if not isinstance(maintainers, list) or any(not m or "," in str(m) for m in maintainers):
            self.add("ERROR", "manifest.toml", "maintainers must be a TOML array of individual non-empty strings.")

        upstream = data.get("upstream", {})
        if isinstance(upstream, dict):
            lic = upstream.get("license", "")
            if not lic or lic == "free":
                self.add("ERROR", "manifest.toml", "upstream.license must be a valid SPDX license ID (not empty or 'free').")
            if str(lic).startswith("LicenseRef-") and not upstream.get("license_url"):
                self.add("ERROR", "manifest.toml", "upstream.license_url is required when using LicenseRef-*.")
            for k in ("website", "demo"):
                if "example.com" in str(upstream.get(k, "")):
                    self.add("ERROR", "manifest.toml", f"Remove placeholder example.com in upstream.{k}.")
            if "yunohost.org" in str(upstream.get("admindoc", "")):
                self.add("ERROR", "manifest.toml", "Remove placeholder yunohost.org in upstream.admindoc.")

        integ = data.get("integration", {})
        if isinstance(integ, dict):
            if integ.get("helpers_version") != "2.1":
                self.add("WARNING", "manifest.toml", 'Set integration.helpers_version = "2.1".')
            ynh_ver = str(integ.get("yunohost", ""))
            if not re.match(r"^>=\s*[0-9]{1,2}(\.[0-9]{1,2}){0,3}$", ynh_ver):
                self.add("ERROR", "manifest.toml", f"Invalid integration.yunohost '{ynh_ver}'.")
            for bkey in ("disk",):
                val = str(integ.get(bkey, ""))
                if val and not re.match(r"^[0-9]*(\.[0-9]*)?[kKmMgG]$", val):
                    self.add("ERROR", "manifest.toml", f"Invalid byte_size '{val}' for integration.{bkey} (use e.g. '50M', not '50MB').")
            ram = integ.get("ram", {})
            if isinstance(ram, dict):
                for rkey in ("build", "runtime"):
                    val = str(ram.get(rkey, ""))
                    if val and not re.match(r"^[0-9]*(\.[0-9]*)?[kKmMgG]$", val):
                        self.add("ERROR", "manifest.toml", f"Invalid byte_size '{val}' for integration.ram.{rkey}.")

        install = data.get("install", {})
        if isinstance(install, dict):
            for qid, qconf in install.items():
                if not isinstance(qconf, dict):
                    continue
                qtype = qconf.get("type", "")
                if qtype not in VALID_QUESTION_TYPES:
                    self.add("ERROR", "manifest.toml", f"Invalid install.{qid}.type '{qtype}'.")
                if (qid, qtype) in CORE_QUESTIONS_NO_ASK and "ask" in qconf:
                    self.add("WARNING", "manifest.toml", f"Do not set 'ask' on generic core question [install.{qid}].")
                elif (qid, qtype) not in CORE_QUESTIONS_NO_ASK and "ask" not in qconf:
                    self.add("WARNING", "manifest.toml", f"Custom question [install.{qid}] must define 'ask.en'.")

        resources = data.get("resources", {})
        if isinstance(resources, dict):
            res_keys = list(resources.keys())
            for rk in res_keys:
                if rk not in VALID_RESOURCE_KEYS:
                    self.add("ERROR", "manifest.toml", f"Unknown resource '[resources.{rk}]' (not a valid Packaging v2 resource).")
            if "database" in resources:
                db_type = resources["database"].get("type")
                if "apt" not in resources or res_keys.index("apt") > res_keys.index("database"):
                    self.add("WARNING", "manifest.toml", "[resources.apt] must appear BEFORE [resources.database] in manifest.toml.")
                apt_raw = str(resources.get("apt", {}).get("packages", ""))
                if db_type == "mysql" and "mariadb-server" not in apt_raw:
                    self.add("WARNING", "manifest.toml", "[resources.apt].packages must include 'mariadb-server' when database.type = 'mysql'.")
                if db_type == "postgresql" and "postgresql" not in apt_raw:
                    self.add("WARNING", "manifest.toml", "[resources.apt].packages must include 'postgresql' when database.type = 'postgresql'.")

            for group_name in ("permissions", "ports"):
                sub = resources.get(group_name, {})
                if isinstance(sub, dict):
                    for sk in sub:
                        if not re.match(r"^.[a-z][a-z0-9_]*$", sk):
                            self.add("ERROR", "manifest.toml", f"[resources.{group_name}.{sk}] key must be >= 2 chars with no hyphens.")

            sources = resources.get("sources", {})
            if isinstance(sources, dict):
                for sid, sconf in sources.items():
                    if isinstance(sconf, dict) and "format" in sconf and sconf["format"] not in VALID_SOURCE_FORMATS:
                        self.add("ERROR", "manifest.toml", f"Invalid format '{sconf['format']}' in [resources.sources.{sid}].")

    def check_scripts(self) -> None:
        scripts_dir = self.root / "scripts"
        if not scripts_dir.is_dir():
            return

        service_add_Signatures: dict[str, str] = {}
        has_service_remove = False

        for spath in sorted(scripts_dir.iterdir()):
            if not spath.is_file():
                continue
            sname = spath.name
            rel = f"scripts/{sname}"
            lines = spath.read_text(encoding="utf-8", errors="replace").splitlines()

            if lines and not lines[0].startswith("#!/bin/bash"):
                self.add("ERROR", rel, "Script must start with #!/bin/bash.")

            helper_line_idx = None
            common_line_idx = None

            for idx, raw_line in enumerate(lines, start=1):
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                loc = f"{rel}:{idx}"

                if re.search(r"\bsource\s+/usr/share/yunohost/helpers\b", stripped):
                    helper_line_idx = idx
                if re.search(r"\bsource\s+(\./)?_common\.sh\b", stripped):
                    common_line_idx = idx
                    if sname in ("backup", "restore"):
                        self.add("ERROR", loc, f"In {sname}, use 'source ../settings/scripts/_common.sh' instead of 'source _common.sh'.")
                if re.search(r"\bsource\s+\.\./settings/scripts/_common\.sh\b", stripped):
                    common_line_idx = idx

                if sname != "config" and re.search(r"\b(ynh_abort_if_errors|set\s+-[eu]+)\b", stripped):
                    self.add("ERROR", loc, "Omit ynh_abort_if_errors / set -eu in Packaging v2 scripts (auto-enabled by core).")
                if re.search(r"\byunohost\s+app\s+setting\b", stripped):
                    self.add("CRITICAL", loc, "Use ynh_app_setting_set/get/delete helpers instead of 'yunohost app setting'.")
                if re.search(r"\b(apt|apt-get)\s+(install|remove|purge)\b", stripped):
                    self.add("ERROR", loc, "Do not call apt install/remove in scripts; use [resources.apt] in manifest.toml.")
                if re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\b", stripped):
                    self.add("ERROR", loc, "Forbidden recursive 'rm -r/-rf'; use ynh_safe_rm (one path per call).")
                if re.search(r"\b(systemctl\s+restart\s+nginx|service\s+nginx\s+restart)\b", stripped):
                    self.add("ERROR", loc, "Never restart nginx; reload via 'ynh_systemctl --service=nginx --action=reload'.")
                if re.search(r"(?<![a-zA-Z0-9_-])exit(?:\s+[0-9]+)?(?:\s|$|;)", stripped):
                    self.add("ERROR", loc, "Do not call 'exit' directly; use ynh_die.")
                if re.search(r"\b(openssl\s+rand|dd\s+if=/dev/urandom)\b", stripped):
                    self.add("ERROR", loc, "Use ynh_string_random instead of openssl rand / /dev/urandom.")
                if sname in ("backup", "_common.sh") and "ynh_script_progression" in stripped:
                    self.add("WARNING", loc, f"Do not use ynh_script_progression in {sname} (use ynh_print_info in backup).")
                if sname == "remove" and re.search(r"(/var/log/|\$data_dir)", stripped):
                    self.add("WARNING", loc, "Do not manually delete /var/log/$app or $data_dir in scripts/remove.")
                if re.search(r"\bsystemctl\s+enable\b", stripped) and "--quiet" not in stripped and " -q" not in stripped:
                    self.add("WARNING", loc, "Pass --quiet to 'systemctl enable'.")

                m_svc = re.search(r"\byunohost\s+service\s+add\s+(.+)$", stripped)
                if m_svc:
                    service_add_Signatures[sname] = m_svc.group(1).strip()
                if re.search(r"\byunohost\s+service\s+remove\b", stripped):
                    has_service_remove = True

                # Inspect all ynh_* tokens on the line
                for token in re.findall(r"\bynh_[a-zA-Z0-9_]+\b", stripped):
                    if token.startswith("ynh_exit_properly"):
                        continue
                    if token in V20_RENAMED_HELPERS:
                        self.add("WARNING", loc, f"Deprecated v2.0 helper '{token}'; rename to '{V20_RENAMED_HELPERS[token]}' in Helpers v2.1.")
                    elif token in RESOURCE_DEPRECATED_HELPERS:
                        self.add("WARNING", loc, f"Helper '{token}' is deprecated in Packaging v2: {RESOURCE_DEPRECATED_HELPERS[token]}.")
                    elif token not in KNOWN_V21_HELPERS:
                        self.add("ERROR", loc, f"Unknown or hallucinated helper '{token}' (not in YunoHost Helpers v2.1).")

                for pos_helper in POSITIONAL_V21_HELPERS_NO_FLAGS:
                    if re.search(rf"\b{pos_helper}\s+--[a-zA-Z0-9_-]+", stripped):
                        self.add(
                            "ERROR",
                            loc,
                            f"Helper '{pos_helper}' takes positional argument(s) in v2.1, NOT '--flag=...' options!",
                        )

            if common_line_idx and helper_line_idx and common_line_idx > helper_line_idx:
                self.add("WARNING", rel, "Source _common.sh BEFORE 'source /usr/share/yunohost/helpers'.")

        if service_add_Signatures and not has_service_remove:
            self.add("ERROR", "scripts/remove", "yunohost service add is used, but 'yunohost service remove' is missing in scripts/remove.")
        if len(set(service_add_Signatures.values())) > 1:
            self.add("WARNING", "scripts/*", f"Inconsistent 'yunohost service add' arguments across scripts: {service_add_Signatures}")

    def check_configs(self) -> None:
        conf_dir = self.root / "conf"
        if not conf_dir.is_dir():
            return
        sso = self.manifest.get("integration", {}).get("sso")

        for cpath in sorted(conf_dir.iterdir()):
            if not cpath.is_file():
                continue
            rel = f"conf/{cpath.name}"
            text = cpath.read_text(encoding="utf-8", errors="replace")

            if "nginx" in cpath.name:
                if re.search(r"location\s+__PATH__\s*\{[^}]*alias\s+__INSTALL_DIR__/", text, re.S):
                    self.add("ERROR", rel, "Alias path-traversal bug: use 'location __PATH__/ {' (with trailing slash) when pairing with 'alias __INSTALL_DIR__/;'!")
                if re.search(r"^\s*add_header\b", text, re.M):
                    self.add("ERROR", rel, "Forbidden 'add_header' in NGINX config; use 'more_set_headers \"Header: value\";'.")
                if re.search(r"if\s*\(\s*\$scheme\s*=\s*http\s*\)", text):
                    self.add("ERROR", rel, "Do not redirect HTTP->HTTPS manually in NGINX (handled by YunoHost).")
                if "proxy_pass" in text:
                    if "proxy_params_with_auth" not in text and "proxy_params_no_auth" not in text:
                        self.add("WARNING", rel, "Include 'proxy_params_no_auth;' or 'proxy_params_with_auth;' with proxy_pass (YunoHost >= 12.1.38).")
                    elif sso is True and "proxy_params_with_auth" not in text:
                        self.add("WARNING", rel, "integration.sso = true should pair with 'include proxy_params_with_auth;'.")
                    elif sso in (False, "not_relevant") and "proxy_params_with_auth" in text:
                        self.add("WARNING", rel, "integration.sso is false/not_relevant, but proxy_params_with_auth is used.")
                if "fastcgi_pass" in text:
                    if "fastcgi_params_with_auth" not in text and "fastcgi_params_no_auth" not in text:
                        self.add("WARNING", rel, "Include 'fastcgi_params_no_auth;' or 'fastcgi_params_with_auth;' with fastcgi_pass (YunoHost >= 12.1.38).")

            if cpath.suffix == ".service":
                for idx, line in enumerate(text.splitlines(), start=1):
                    s = line.strip()
                    if s.startswith("#"):
                        continue
                    if s.startswith("Environment=") and re.search(r"(pass|secret|key|token)", s, re.I):
                        self.add("ERROR", f"{rel}:{idx}", "Never place secrets/passwords/keys in world-readable systemd Environment=; use EnvironmentFile=.")
                    if re.match(r"^User=(root|www-data)\b", s):
                        self.add("WARNING", f"{rel}:{idx}", "Run systemd service as User=__APP__ instead of root or www-data.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a YunoHost *_ynh package against Packaging v2 / Helpers v2.1 rules.")
    parser.add_argument("package_dir", help="Path to the *_ynh package directory")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on WARNINGs as well (Level 7 mode)")
    args = parser.parse_args()

    pkg = Path(args.package_dir).resolve()
    if not pkg.is_dir():
        raise SystemExit(f"Directory not found: {pkg}")

    findings = PackageAuditor(pkg).run()
    counts = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
        print(f"[{f.severity}] {f.location}: {f.message}")

    print(
        f"\nSummary for {pkg.name}: "
        f"{counts['CRITICAL']} critical, {counts['ERROR']} errors, {counts['WARNING']} warnings, {counts['INFO']} info"
    )

    if counts["CRITICAL"] > 0 or counts["ERROR"] > 0 or (args.strict and counts["WARNING"] > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
