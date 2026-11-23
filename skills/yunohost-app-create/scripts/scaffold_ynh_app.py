#!/usr/bin/env python3
"""Scaffold a clean, package_linter-compliant YunoHost Packaging v2 (Helpers v2.1) app."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path

STACKS = ("proxy", "php", "nodejs", "python", "go", "static")
DATABASES = ("none", "mysql", "postgresql")


def validate_inputs(app_id: str, name: str) -> None:
    if not re.match(r"^[a-z0-9]((_|-)?[a-z0-9])+$", app_id) or app_id.endswith("_ynh"):
        raise SystemExit(
            f"Invalid --id '{app_id}': must be lowercase alphanumeric/hyphen/underscore and NOT end with '_ynh'."
        )
    if len(name) > 22:
        raise SystemExit(
            f"Invalid --name '{name}' ({len(name)} chars): package_linter requires <= 22 characters."
        )


def write_file(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def build_manifest(
    app_id: str,
    name: str,
    description: str,
    version: str,
    maintainer: str,
    license_spdx: str,
    upstream_code: str,
    upstream_website: str,
    stack: str,
    database: str,
    sso: str,
    ldap: str,
    root_only: bool,
) -> str:
    sso_toml = "true" if sso == "true" else ("false" if sso == "false" else '"not_relevant"')
    ldap_toml = "true" if ldap == "true" else ("false" if ldap == "false" else '"not_relevant"')
    apt_pkgs: list[str] = []
    if database == "mysql":
        apt_pkgs.append("mariadb-server")
    elif database == "postgresql":
        apt_pkgs.append("postgresql")

    if stack == "php":
        apt_pkgs.extend(
            [
                "php8.3-fpm",
                "php8.3-cli",
                "php8.3-mbstring",
                "php8.3-xml",
                "php8.3-zip",
                "php8.3-curl",
            ]
        )
        if database == "mysql":
            apt_pkgs.append("php8.3-mysql")
        elif database == "postgresql":
            apt_pkgs.append("php8.3-pgsql")
    elif stack == "python":
        apt_pkgs.extend(["python3", "python3-venv", "python3-pip"])

    path_block = ""
    if not root_only:
        path_block = f"""
    [install.path]
    type = "path"
    default = "/{app_id}"
"""

    resources_extra: list[str] = []
    if stack in ("proxy", "nodejs", "python", "go"):
        resources_extra.append("    [resources.ports]\n")
    if stack == "nodejs":
        resources_extra.append('    [resources.nodejs]\n    version = "22"\n')
    elif stack == "go":
        resources_extra.append('    [resources.go]\n    version = "1.23"\n')

    if apt_pkgs:
        pkgs_str = ", ".join(f'"{p}"' for p in apt_pkgs)
        resources_extra.append(f"    [resources.apt]\n    packages = [{pkgs_str}]\n")

    if database in ("mysql", "postgresql"):
        resources_extra.append(f'    [resources.database]\n    type = "{database}"\n')

    website_line = f'website = "{upstream_website}"\n' if upstream_website else ""
    code_line = f'code = "{upstream_code}"\n' if upstream_code else ""
    autoupdate_line = (
        '    autoupdate.strategy = "latest_github_tag"\n'
        if "github.com/" in upstream_code
        else ""
    )

    return f"""#:schema https://raw.githubusercontent.com/YunoHost/apps/main/schemas/manifest.v2.schema.json

packaging_format = 2

id = "{app_id}"
name = "{name}"
description.en = "{description}"

version = "{version}"

maintainers = ["{maintainer}"]

[upstream]
license = "{license_spdx}"
{website_line}{code_line}
[integration]
yunohost = ">= 12.1.38"
helpers_version = "2.1"
architectures = "all"
multi_instance = true
ldap = {ldap_toml}
sso = {sso_toml}
disk = "100M"
ram.build = "250M"
ram.runtime = "100M"

[install]
    [install.domain]
    type = "domain"
{path_block}
    [install.init_main_permission]
    type = "group"
    default = "visitors"

[resources]
    [resources.sources.main]
    url = "{upstream_code or 'https://github.com/org/repo'}/archive/refs/tags/v{version.split('~')[0]}.tar.gz"
    sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
{autoupdate_line}
    [resources.system_user]

    [resources.install_dir]

    [resources.data_dir]

    [resources.permissions]
    main.url = "/"

{chr(10).join(resources_extra).rstrip()}
"""


def scaffold(args: argparse.Namespace) -> Path:
    validate_inputs(args.id, args.name)
    out = Path(args.output or f"./{args.id}_ynh").resolve()
    if out.exists() and any(out.iterdir()) and not args.force:
        raise SystemExit(f"Target directory {out} is not empty (pass --force to overwrite).")

    is_daemon = args.stack in ("proxy", "nodejs", "python", "go")
    is_php = args.stack == "php"
    sso_suffix = "with_auth" if args.sso == "true" else "no_auth"

    write_file(
        out / "manifest.toml",
        build_manifest(
            app_id=args.id,
            name=args.name,
            description=args.description,
            version=args.version,
            maintainer=args.maintainer,
            license_spdx=args.license,
            upstream_code=args.code,
            upstream_website=args.website,
            stack=args.stack,
            database=args.database,
            sso=args.sso,
            ldap=args.ldap,
            root_only=args.root_only,
        ),
    )

    write_file(
        out / ".editorconfig",
        """root = true

[*]
charset = utf-8
end_of_line = lf
indent_size = 4
indent_style = space
insert_final_newline = true
trim_trailing_whitespace = true
""",
    )

    write_file(
        out / ".gitattributes",
        """tests.toml linguist-language=toml
config_panel.toml linguist-language=toml
*README*.md linguist-generated=true
""",
    )

    write_file(
        out / "LICENSE",
        f"""MIT License

Copyright (c) 2026 {args.maintainer}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    )

    write_file(
        out / "README.md",
        f"""<!--
N.B.: This README was automatically generated by <https://github.com/YunoHost/apps/tree/master/tools/readme_generator>
It shall NOT be edited by hand.
-->

# {args.name} for YunoHost

[![Integration level](https://apps.yunohost.org/badge/integration/{args.id})](https://ci-apps.yunohost.org/ci/apps/{args.id}/)
![Working status](https://apps.yunohost.org/badge/state/{args.id})
![Maintenance status](https://apps.yunohost.org/badge/maintained/{args.id})

[![Install {args.name} with YunoHost](https://install-app.yunohost.org/install-with-yunohost.svg)](https://install-app.yunohost.org/?app={args.id})

*[Read this README in other languages.](./ALL_README.md)*

> *This package allows you to install {args.name} quickly and simply on a YunoHost server.*
> *If you don't have YunoHost, please consult [the guide](https://yunohost.org/install) to learn how to install it.*

## Overview

{args.description}

**Shipped version:** {args.version}
""",
    )

    write_file(
        out / "tests.toml",
        """#:schema https://raw.githubusercontent.com/YunoHost/apps/main/schemas/tests.v1.schema.json

test_format = 1.0

[default]
""",
    )

    write_file(
        out / "doc/DESCRIPTION.md",
        f"{args.name} is a self-hosted application.\n\n### Features\n\n- Self-hosted deployment integrated with YunoHost\n",
    )
    write_file(
        out / "doc/ADMIN.md",
        f"The application files are stored in `__INSTALL_DIR__` and persistent data in `__DATA_DIR__`.\n",
    )

    # NGINX config
    if is_daemon:
        nginx_conf = f"""#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;
location __PATH__/ {{

  proxy_pass http://127.0.0.1:__PORT__/;
  include proxy_params_{sso_suffix};
  proxy_redirect off;
}}
"""
    elif is_php:
        nginx_conf = f"""#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;
location __PATH__/ {{

  alias __INSTALL_DIR__/;

  index index.php;
  client_max_body_size 50M;

  try_files $uri $uri/ __PATH__/index.php?$args;
  location ~ [^/]\\.php(/|$) {{
    fastcgi_pass unix:/var/run/php/php__PHP_VERSION__-fpm-__APP__.sock;
    include fastcgi_params_{sso_suffix};
  }}
}}
"""
    else:
        nginx_conf = """#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;
location __PATH__/ {

  alias __INSTALL_DIR__/;

  index index.html;
  try_files $uri $uri/ __PATH__/index.html;
}
"""
    write_file(out / "conf/nginx.conf", nginx_conf)

    if is_daemon:
        env_lines = ['APP_URL="https://__DOMAIN____PATH__"', "PORT=__PORT__", 'HOST="127.0.0.1"', 'DATA_DIR="__DATA_DIR__"']
        if args.database != "none":
            env_lines.extend(['DB_NAME="__DB_NAME__"', 'DB_USER="__DB_USER__"', 'DB_PASSWORD="__DB_PWD__"'])
        write_file(out / "conf/app.env", "\n".join(env_lines) + "\n")

        exec_start = f"__INSTALL_DIR__/{args.id}"
        extra_env = ""
        if args.stack == "nodejs":
            exec_start = "__NODEJS_DIR__/node __INSTALL_DIR__/server.js"
            extra_env = 'Environment="PATH=__PATH_WITH_NODEJS__"\nEnvironment="NODE_ENV=production"\n'
        elif args.stack == "python":
            exec_start = "__INSTALL_DIR__/venv/bin/python -m app"

        write_file(
            out / "conf/systemd.service",
            f"""[Unit]
Description={args.name} service
After=network.target

[Service]
Type=simple
User=__APP__
Group=__APP__
WorkingDirectory=__INSTALL_DIR__/
{extra_env}EnvironmentFile=__INSTALL_DIR__/.env
ExecStart={exec_start}
Restart=on-failure
StandardOutput=append:/var/log/__APP__/__APP__.log
StandardError=inherit

NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK
RestrictNamespaces=yes
RestrictRealtime=yes
DevicePolicy=closed
ProtectClock=yes
ProtectHostname=yes
ProtectProc=invisible
ProtectSystem=full
ProtectControlGroups=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
LockPersonality=yes
SystemCallArchitectures=native
SystemCallFilter=~@clock @debug @module @mount @obsolete @reboot @setuid @swap @cpu-emulation @privileged

CapabilityBoundingSet=~CAP_RAWIO CAP_MKNOD
CapabilityBoundingSet=~CAP_AUDIT_CONTROL CAP_AUDIT_READ CAP_AUDIT_WRITE
CapabilityBoundingSet=~CAP_SYS_BOOT CAP_SYS_TIME CAP_SYS_MODULE CAP_SYS_PACCT
CapabilityBoundingSet=~CAP_LEASE CAP_LINUX_IMMUTABLE CAP_IPC_LOCK
CapabilityBoundingSet=~CAP_BLOCK_SUSPEND CAP_WAKE_ALARM
CapabilityBoundingSet=~CAP_SYS_TTY_CONFIG
CapabilityBoundingSet=~CAP_MAC_ADMIN CAP_MAC_OVERRIDE
CapabilityBoundingSet=~CAP_NET_ADMIN CAP_NET_BROADCAST CAP_NET_RAW
CapabilityBoundingSet=~CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_SYSLOG

[Install]
WantedBy=multi-user.target
""",
        )

    # Scripts
    write_file(
        out / "scripts/_common.sh",
        """#!/bin/bash

#=================================================
# COMMON VARIABLES AND CUSTOM HELPERS
#=================================================
""",
        executable=True,
    )

    build_step = ""
    if args.stack == "nodejs":
        build_step = 'pushd "$install_dir"\n    ynh_exec_as_app npm ci --omit=dev\npopd\n'
    elif args.stack == "python":
        build_step = (
            'ynh_exec_as_app python3 -m venv "$install_dir/venv"\n'
            'ynh_exec_as_app "$install_dir/venv/bin/pip" install --upgrade pip wheel\n'
            'ynh_exec_as_app "$install_dir/venv/bin/pip" install --no-cache-dir -r "$install_dir/requirements.txt"\n'
        )
    elif args.stack == "go":
        build_step = f'pushd "$install_dir"\n    ynh_exec_as_app go build -o "{args.id}" .\npopd\n'

    chown_group = "$app" if is_daemon else "www-data"

    install_conf = ""
    if is_daemon:
        install_conf = """#=================================================
# APP INITIAL CONFIGURATION
#=================================================
ynh_script_progression "Adding $app's configuration files..."

ynh_config_add --template="app.env" --destination="$install_dir/.env"
chmod 400 "$install_dir/.env"
chown "$app:$app" "$install_dir/.env"
"""

    sys_conf_lines = []
    if is_php:
        sys_conf_lines.append("ynh_config_add_phpfpm")
    sys_conf_lines.append("ynh_config_add_nginx")
    if is_daemon:
        sys_conf_lines.extend(
            [
                "ynh_config_add_systemd",
                f'yunohost service add "$app" --description="{args.name} service" --log="/var/log/$app/$app.log"',
                "ynh_config_add_logrotate",
            ]
        )
    sys_conf_block = "\n\n".join(sys_conf_lines)

    start_block = ""
    stop_block = ""
    if is_daemon:
        start_block = """
#=================================================
# START SYSTEMD SERVICE
#=================================================
ynh_script_progression "Starting $app's systemd service..."

ynh_systemctl --service="$app" --action="start"
"""
        stop_block = """#=================================================
# STOP SYSTEMD SERVICE
#=================================================
ynh_script_progression "Stopping $app's systemd service..."

ynh_systemctl --service="$app" --action="stop"

"""

    php_init = ""
    php_compat = ""
    if is_php:
        php_init = """#=================================================
# INITIALIZE AND STORE SETTINGS
#=================================================

ynh_app_setting_set --key=php_upload_max_filesize --value=50M

"""
        php_compat = """#=================================================
# ENSURE DOWNWARD COMPATIBILITY
#=================================================
ynh_script_progression "Ensuring downward compatibility..."

ynh_app_setting_set_default --key=php_upload_max_filesize --value=50M

"""

    write_file(
        out / "scripts/install",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source _common.sh
source /usr/share/yunohost/helpers

{php_init}#=================================================
# DOWNLOAD, CHECK AND UNPACK SOURCE
#=================================================
ynh_script_progression "Setting up source files..."

ynh_setup_source --dest_dir="$install_dir"
{build_step}chown -R "$app:{chown_group}" "$install_dir"

{install_conf}#=================================================
# SYSTEM CONFIGURATION
#=================================================
ynh_script_progression "Adding system configurations related to $app..."

{sys_conf_block}
{start_block}
#=================================================
# END OF SCRIPT
#=================================================

ynh_script_progression "Installation of $app completed"
""",
        executable=True,
    )

    keep_arg = ' --keep=".env"' if is_daemon else ""
    write_file(
        out / "scripts/upgrade",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source _common.sh
source /usr/share/yunohost/helpers

{stop_block}{php_compat}#=================================================
# DOWNLOAD, CHECK AND UNPACK SOURCE
#=================================================
ynh_script_progression "Upgrading source files..."

ynh_setup_source --dest_dir="$install_dir" --full_replace{keep_arg}
{build_step}chown -R "$app:{chown_group}" "$install_dir"

{install_conf.replace("APP INITIAL CONFIGURATION", "UPDATE A CONFIG FILE").replace("Adding", "Updating")}#=================================================
# REAPPLY SYSTEM CONFIGURATION
#=================================================
ynh_script_progression "Upgrading system configurations related to $app..."

{sys_conf_block}
{start_block}
#=================================================
# END OF SCRIPT
#=================================================

ynh_script_progression "Upgrade of $app completed"
""",
        executable=True,
    )

    remove_lines = []
    if is_daemon:
        remove_lines.extend(
            [
                "ynh_config_remove_logrotate",
                'if ynh_hide_warnings yunohost service status "$app" >/dev/null; then\n    yunohost service remove "$app"\nfi\nynh_config_remove_systemd',
            ]
        )
    remove_lines.append("ynh_config_remove_nginx")
    if is_php:
        remove_lines.append("ynh_config_remove_phpfpm")

    write_file(
        out / "scripts/remove",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source _common.sh
source /usr/share/yunohost/helpers

#=================================================
# REMOVE SYSTEM CONFIGURATION
#=================================================
ynh_script_progression "Removing system configurations related to $app..."

{chr(10).join(remove_lines)}

#=================================================
# END OF SCRIPT
#=================================================

ynh_script_progression "Removal of $app completed"
""",
        executable=True,
    )

    backup_sys = ['ynh_backup "/etc/nginx/conf.d/$domain.d/$app.conf"']
    restore_sys = ['ynh_restore "/etc/nginx/conf.d/$domain.d/$app.conf"']
    if is_php:
        backup_sys.insert(0, 'ynh_backup "/etc/php/$php_version/fpm/pool.d/$app.conf"')
        restore_sys.insert(0, 'ynh_restore "/etc/php/$php_version/fpm/pool.d/$app.conf"')
    if is_daemon:
        backup_sys.extend(
            [
                'ynh_backup "/etc/systemd/system/$app.service"',
                'ynh_backup "/etc/logrotate.d/$app"',
                'ynh_backup "/var/log/$app/"',
            ]
        )
        restore_sys.extend(
            [
                'ynh_restore "/etc/systemd/system/$app.service"\nsystemctl enable "$app.service" --quiet',
                f'yunohost service add "$app" --description="{args.name} service" --log="/var/log/$app/$app.log"',
                'ynh_restore "/etc/logrotate.d/$app"',
                'ynh_restore "/var/log/$app/"',
            ]
        )

    db_backup = ""
    db_restore = ""
    if args.database == "mysql":
        db_backup = '\nynh_print_info "Backing up the MySQL database..."\nynh_mysql_dump_db > db.sql\n'
        db_restore = '\nynh_script_progression "Restoring the MySQL database..."\nynh_mysql_db_shell < ./db.sql\n'
    elif args.database == "postgresql":
        db_backup = '\nynh_print_info "Backing up the PostgreSQL database..."\nynh_psql_dump_db > db.sql\n'
        db_restore = '\nynh_script_progression "Restoring the PostgreSQL database..."\nynh_psql_db_shell < ./db.sql\n'

    write_file(
        out / "scripts/backup",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source ../settings/scripts/_common.sh
source /usr/share/yunohost/helpers

ynh_print_info "Declaring files to be backed up..."

#=================================================
# BACKUP THE APP MAIN DIR AND DATA DIR
#=================================================

ynh_backup "$install_dir"
ynh_backup "$data_dir"

#=================================================
# BACKUP SYSTEM CONFIGURATION
#=================================================

{chr(10).join(backup_sys)}
{db_backup}
#=================================================
# END OF SCRIPT
#=================================================

ynh_print_info "Backup script completed for $app."
""",
        executable=True,
    )

    restore_reload = ['ynh_systemctl --service=nginx --action=reload']
    if is_php:
        restore_reload.insert(0, 'ynh_systemctl --service="php$php_version-fpm" --action=reload')
    if is_daemon:
        restore_reload.insert(0, 'ynh_systemctl --service="$app" --action="start"')

    write_file(
        out / "scripts/restore",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source ../settings/scripts/_common.sh
source /usr/share/yunohost/helpers

#=================================================
# RESTORE THE APP MAIN DIR AND DATA DIR
#=================================================
ynh_script_progression "Restoring the app main directory..."

ynh_restore "$install_dir"
chown -R "$app:{chown_group}" "$install_dir"

ynh_script_progression "Restoring the data directory..."

ynh_restore "$data_dir"
chown -R "$app:$app" "$data_dir"
{db_restore}
#=================================================
# RESTORE SYSTEM CONFIGURATION
#=================================================
ynh_script_progression "Restoring system configurations related to $app..."

{chr(10).join(restore_sys)}

#=================================================
# RELOAD SERVICES
#=================================================
ynh_script_progression "Reloading NGINX web server and services..."

{chr(10).join(restore_reload)}

#=================================================
# END OF SCRIPT
#=================================================

ynh_script_progression "Restoration completed for $app"
""",
        executable=True,
    )

    change_url_conf = ""
    if is_daemon:
        change_url_conf = """ynh_config_add --template="app.env" --destination="$install_dir/.env"
chmod 400 "$install_dir/.env"
chown "$app:$app" "$install_dir/.env"
"""

    write_file(
        out / "scripts/change_url",
        f"""#!/bin/bash

#=================================================
# IMPORT GENERIC HELPERS
#=================================================

source _common.sh
source /usr/share/yunohost/helpers

{stop_block}#=================================================
# MODIFY URL IN NGINX CONF
#=================================================
ynh_script_progression "Updating NGINX web server configuration..."

ynh_config_change_url_nginx

{change_url_conf}{start_block}
#=================================================
# END OF SCRIPT
#=================================================

ynh_script_progression "Change of URL completed for $app"
""",
        executable=True,
    )

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a YunoHost Packaging v2 (Helpers v2.1) app package.")
    parser.add_argument("--id", required=True, help="App ID (lowercase, e.g. 'myapp', without '_ynh')")
    parser.add_argument("--name", required=True, help="Display name (max 22 chars)")
    parser.add_argument(
        "--description",
        default="Self-hosted web application packaged for easy deployment",
        help="Short description (5..150 chars, do NOT mention 'for YunoHost')",
    )
    parser.add_argument("--version", default="1.0.0~ynh1", help="Initial package version (<ver>~ynh1)")
    parser.add_argument("--maintainer", default="maintainer", help="Maintainer handle")
    parser.add_argument("--license", default="MIT", help="Upstream SPDX license ID")
    parser.add_argument("--code", default="", help="Upstream source code repository URL")
    parser.add_argument("--website", default="", help="Upstream project website URL")
    parser.add_argument("--stack", choices=STACKS, default="proxy", help="Application stack preset")
    parser.add_argument("--database", choices=DATABASES, default="none", help="Database resource to provision")
    parser.add_argument("--sso", choices=("true", "false", "not_relevant"), default="false", help="SSOwat auto-login")
    parser.add_argument("--ldap", choices=("true", "false", "not_relevant"), default="false", help="LDAP integration")
    parser.add_argument("--root-only", action="store_true", help="Omit [install.path] for root-domain-only apps")
    parser.add_argument("--output", default="", help="Output directory (defaults to ./<id>_ynh)")
    parser.add_argument("--force", action="store_true", help="Overwrite into non-empty output directory")

    parsed = parser.parse_args()
    target = scaffold(parsed)
    print(f"Scaffolded YunoHost package at: {target}")


if __name__ == "__main__":
    main()
