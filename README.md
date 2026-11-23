# YunoHost App Maintainer — GitHub Copilot Plugin (`yunohost_app_maintainer`)

A comprehensive **GitHub Copilot Agent Plugin** (conforming to the [Agent Plugins 1.0](https://agent-plugins.org/) standard + `com.github.copilot` extensions) that helps developers and maintainers **create, update, migrate, lint, test, and publish YunoHost application packages (`*_ynh`)**.

Built directly from the official [YunoHost Developer & Packaging Documentation](https://doc.yunohost.org/en/dev/), [`YunoHost/example_ynh`](https://github.com/YunoHost/example_ynh), [`YunoHost/package_linter`](https://github.com/YunoHost/package_linter), [`YunoHost/package_check`](https://github.com/YunoHost/package_check), and [`YunoHost/apps`](https://github.com/YunoHost/apps) JSON schemas—targeting **Packaging v2** (`manifest.toml`) and **Helpers v2.1** (`yunohost >= 12.1.38`) with zero hallucinated helpers.

> **Note on Plugin Slug**: Per the Agent Plugins 1.0 & Copilot CLI naming specification (lowercase ASCII letters, digits, and hyphens only; underscores are disallowed in `plugin.json` and `SKILL.md` IDs), the technical package identifier is **`yunohost-app-maintainer`**.

---

## What's Included

```text
yunohost-app-maintainer/
├── plugin.json                                     # Agent Plugins 1.0 manifest
├── .github/plugin/marketplace.json                 # Self-hosted marketplace catalog entry
├── com.github.copilot/                             # Copilot-specific customizations
│   ├── agents/
│   │   └── yunohost-app-maintainer.agent.md        # Custom Maintainer & Reviewer persona
│   ├── rules/
│   │   └── yunohost-packaging.instructions.md      # Auto-applied rules for *_ynh files
│   └── commands/
│       ├── ynh-new-app.prompt.md                   # /ynh-new-app slash command
│       ├── ynh-upgrade-app.prompt.md               # /ynh-upgrade-app slash command
│       └── ynh-review-app.prompt.md                # /ynh-review-app slash command
└── skills/                                         # Portable Agent Skills (VS Code, CLI, Copilot App)
    ├── yunohost-app-create/
    │   ├── SKILL.md                                # New package workflow
    │   ├── scripts/scaffold_ynh_app.py             # Zero-dependency *_ynh generator CLI
    │   ├── assets/                                 # NGINX, systemd, config_panel & tests templates
    │   └── references/                             # manifest, 12 resources, 96 v2.1 helpers, SSO/LDAP, catalog
    ├── yunohost-app-update/
    │   ├── SKILL.md                                # Version bump, autoupdate & v1/v2.0 -> v2.1 migration
    │   ├── scripts/fetch_source_sha256.py          # Streaming SHA-256 calculator & TOML generator
    │   └── references/                             # v1->v2 & v2.0->v2.1 rename matrix, autoupdate & CI bots
    └── yunohost-app-lint-and-test/
        ├── SKILL.md                                # Linting, Quality Levels 0-8, package_check & Core dev
        ├── scripts/check_ynh_package.py            # Zero-dependency static validator & helper checker
        └── references/                             # package_linter rulebook, tests.toml, ynh-dev & Core
```

| Component | Name / ID | Purpose |
|---|---|---|
| **Custom Agent** | `yunohost-app-maintainer` | Dedicated YunoHost packaging & review specialist enforcing `example_ynh` conventions and Level 7/8 quality |
| **Skill** | `yunohost-app-create` | Scaffold and implement brand-new Packaging v2 (`helpers_version = "2.1"`) apps, NGINX/systemd, SSO/LDAP, config panels, hooks, docs, and catalog PRs |
| **Skill** | `yunohost-app-update` | Upgrade upstream versions, compute SHA-256 hashes, configure `autoupdate`, ensure downward compatibility, or migrate v1 / Helpers v2.0 -> v2.1 |
| **Skill** | `yunohost-app-lint-and-test` | Audit packages with `check_ynh_package.py` / `package_linter`, write `tests.toml`, run `package_check` / `ynh-dev`, and inspect YunoHost Core |
| **File Rules** | `yunohost-packaging` | Automatically injects Packaging v2 & Helpers v2.1 guardrails whenever editing `manifest.toml`, `scripts/*`, `conf/*.conf`, `conf/*.service`, `config_panel.toml`, or `tests.toml` |
| **Slash Prompts** | `/ynh-new-app`, `/ynh-upgrade-app`, `/ynh-review-app` | One-step task launchers in Copilot Chat |

---

## How to Install

### Prerequisites
- **GitHub Copilot** in **VS Code** (with `"chat.plugins.enabled": true`) and/or **GitHub Copilot CLI** (`>= 1.0`).
- **Python 3.11+** (uses standard-library `tomllib`—no `pip install` needed for the bundled helper scripts).

---

### Option 1: Install in Visual Studio Code

#### A. Install from Git Repository or Local Folder (UI)
1. Ensure `"chat.plugins.enabled": true` is enabled in your VS Code settings.
2. Open the **Command Palette** (`Ctrl+Shift+P` / `Cmd+Shift+P`) and run **`Chat: Install Plugin from Source`** *(or open **Chat: Open Customizations** -> **Plugins** -> click **`+`** next to **User** or **Workspace**)*.
3. Enter either:
   - Your **Git repository URL** (for example `https://github.com/<your-org>/yunohost-app-maintainer`), or
   - The **local directory path** to this repository (for example `/home/user/ynh/skill_ynh`).

#### B. Register a Live Local Checkout in `settings.json` (Best for Plugin Development)
Add `chat.pluginLocations` to your VS Code User or Remote `settings.json` so edits take effect immediately without reinstalling:

```json
{
  "chat.plugins.enabled": true,
  "chat.pluginLocations": {
    "/absolute/path/to/skill_ynh": true
  }
}
```

---

### Option 2: Install in GitHub Copilot CLI

*(Note: Plugins installed via a local marketplace load live from disk and are shared with Copilot Agent Host sessions in VS Code!)*

```bash
# Register the plugin's marketplace and install (recommended, live-reloads on new sessions):
copilot plugin marketplace add /path/to/skill_ynh
copilot plugin install yunohost-app-maintainer@yunohost-plugins

# Or register from GitHub and install:
copilot plugin marketplace add <owner>/<repo>
copilot plugin install yunohost-app-maintainer@yunohost-plugins

# Verify installation and skills:
copilot plugin list
copilot skill list
```

When developing locally, you can also mount the plugin per session without installing:

```bash
copilot --plugin-dir /path/to/skill_ynh
```

To update or uninstall later:

```bash
# Re-install local changes into cache:
copilot plugin install /path/to/skill_ynh

# Uninstall by plugin manifest name:
copilot plugin uninstall yunohost-app-maintainer
```

---

### Option 3: Share Across a Team / Repository (`.github/copilot/settings.json`)

This repository includes `.github/plugin/marketplace.json`, so you can register it as a marketplace for any YunoHost packaging workspace:

```json
{
  "extraKnownMarketplaces": {
    "yunohost-plugins": {
      "source": {
        "source": "github",
        "repo": "<owner>/<repo>"
      }
    }
  },
  "enabledPlugins": {
    "yunohost-app-maintainer@yunohost-plugins": true
  }
}
```

---

### Option 4: Standalone Skills Copy (Without Plugin System)

If your client only supports standalone Agent Skills (`SKILL.md`):

```bash
mkdir -p ~/.copilot/skills
cp -r /path/to/skill_ynh/skills/* ~/.copilot/skills/
```

---

## How to Use

### 1. Select the Custom Agent (`yunohost-app-maintainer`)
- **In VS Code Chat**: Open the Agent picker dropdown in the Chat panel and select **`yunohost-app-maintainer`**.
- **In GitHub Copilot CLI**: Run `/agent` and choose **`yunohost-app-maintainer`**.

### 2. Invoke Skills & Slash Commands in Chat
Type `/` in Copilot Chat to invoke any bundled workflow directly:

- **`/yunohost-app-create`** *(or `/ynh-new-app`)* — Create a new `*_ynh` package from scratch:
  ```text
  /yunohost-app-create Package https://github.com/louislam/uptime-kuma as uptime-kuma_ynh (Node.js 22 daemon behind NGINX reverse proxy, subpath + root support).
  ```
- **`/yunohost-app-update`** *(or `/ynh-upgrade-app`)* — Bump an existing package or migrate v1/v2.0 -> v2/v2.1:
  ```text
  /yunohost-app-update Update ./myapp_ynh to upstream v2.5.1, update SHA-256 checksums, configure latest_github_release autoupdate, and ensure downward compatibility in scripts/upgrade.
  ```
  ```text
  /yunohost-app-update Migrate ./legacyapp_ynh from Helpers v2.0 to Helpers v2.1 and modern NGINX proxy_params_no_auth.
  ```
- **`/yunohost-app-lint-and-test`** *(or `/ynh-review-app`)* — Audit a package for Level 7/8 quality:
  ```text
  /yunohost-app-lint-and-test Audit ./myapp_ynh for package_linter errors/warnings, helper hallucinations, NGINX/systemd security issues, and backup/restore symmetry.
  ```

### 3. Natural-Language Prompts (Auto-Triggered)
Even in the default Copilot agent, skills and file-scoped instructions load automatically when working on `*_ynh` repositories:
- *"Add LDAP (`dc=yunohost,dc=org`) and SSOwat HTTP header authentication to `manifest.toml` and `conf/nginx.conf`."*
- *"Create a `config_panel.toml` binding `ALLOW_SIGNUP` and `SMTP_HOST` in `__INSTALL_DIR__/.env` and restarting `__APP__`."*
- *"Add a `hooks/post_cert_update` hook to reload TLS certificates for my daemon."*
- *"Write `curl_tests` in `tests.toml` for public and SSO-authenticated endpoints."*

### 4. Run the Bundled CLI Scripts Directly

All three Python scripts run standalone with Python 3.11+ and zero third-party packages:

```bash
# 1. Scaffold a new YunoHost v2 / Helpers v2.1 package (--stack: proxy|php|nodejs|python|go|static)
python3 skills/yunohost-app-create/scripts/scaffold_ynh_app.py \
  --id mywiki \
  --name "My Wiki" \
  --description "Lightweight Markdown wiki for small teams" \
  --stack nodejs \
  --database postgresql \
  --code "https://github.com/example-org/mywiki" \
  --output ./mywiki_ynh

# 2. Stream-download upstream release URLs and print [resources.sources.<id>] TOML with SHA-256
python3 skills/yunohost-app-update/scripts/fetch_source_sha256.py \
  --arch amd64="https://github.com/org/app/releases/download/v1.4.0/app-linux-amd64.tar.gz" \
  --arch arm64="https://github.com/org/app/releases/download/v1.4.0/app-linux-arm64.tar.gz"

# 3. Statically lint a *_ynh package (--strict fails on Warnings too, matching Level 7 requirements)
python3 skills/yunohost-app-lint-and-test/scripts/check_ynh_package.py --strict ./mywiki_ynh
```

---

## Official YunoHost Reference Links

### Developer & Packaging Documentation (`doc.yunohost.org/en/dev/`)
- **Overview & Contributing**
  - [Contributing to YunoHost](https://doc.yunohost.org/en/dev/) *(incl. generative AI & code-ownership policy)*
  - [Working with Git / GitHub](https://doc.yunohost.org/en/dev/git)
  - [Working on the Documentation](https://doc.yunohost.org/en/dev/doc)
  - [Working on Translations (Weblate)](https://doc.yunohost.org/en/dev/translation)
- **Application Packaging (`doc.yunohost.org/en/dev/packaging/`)**
  - [Application Packaging Introduction & Philosophy](https://doc.yunohost.org/en/dev/packaging/)
  - [App Package Structure](https://doc.yunohost.org/en/dev/packaging/structure)
  - [`manifest.toml` Specification](https://doc.yunohost.org/en/dev/packaging/manifest)
  - [App Resources (`sources`, `system_user`, `install_dir`, `data_dir`, `permissions`, `ports`, `apt`, `database`, `nodejs`, `ruby`, `go`, `composer`)](https://doc.yunohost.org/en/dev/packaging/resources)
  - [App Lifecycle Scripts (`install`, `upgrade`, `remove`, `backup`, `restore`, `change_url`)](https://doc.yunohost.org/en/dev/packaging/scripts/)
  - [App Helpers v2.1 (Current Recommended)](https://doc.yunohost.org/en/dev/packaging/scripts/helpers_v2.1)
  - [App Helpers v2.0 (Legacy Reference)](https://doc.yunohost.org/en/dev/packaging/scripts/helpers_v2.0)
  - [Documenting Apps (`DESCRIPTION.md`, `ADMIN.md`, `PRE/POST_INSTALL`, `PRE/POST_UPGRADE`, Screenshots)](https://doc.yunohost.org/en/dev/packaging/doc)
  - [Testing Your App (`yunohost app install`, `package_linter`, `package_check`, `tests.toml`, Quality Levels 0–8)](https://doc.yunohost.org/en/dev/packaging/test)
  - [Publishing Your App on the Catalog (`apps.toml`)](https://doc.yunohost.org/en/dev/packaging/publish)
  - [Catalog Inclusion & Anti-Features Policy](https://doc.yunohost.org/en/dev/packaging/policy)
- **Advanced Packaging (`doc.yunohost.org/en/dev/packaging/advanced/`)**
  - [Config Panels (`config_panel.toml` & `scripts/config`)](https://doc.yunohost.org/en/dev/packaging/advanced/config_panels)
  - [SSOwat & LDAP Integration (`dc=yunohost,dc=org`, HTTP Headers, OIDC Notes)](https://doc.yunohost.org/en/dev/packaging/advanced/sso_ldap_integration)
  - [YunoHost Hooks (`hooks/`)](https://doc.yunohost.org/en/dev/packaging/advanced/hooks)
  - [Advanced Packagers (Branches, CI Bots `!testme` / `!bump`, `autoupdate`)](https://doc.yunohost.org/en/dev/packaging/advanced/advanced_packagers)
  - [Packaging v2 Overview & v1 -> v2 Migration](https://doc.yunohost.org/en/dev/packaging/advanced/packaging_v2)
- **Misc Packaging Guides (`doc.yunohost.org/en/dev/packaging/misc/`)**
  - [Use Git to Package Apps](https://doc.yunohost.org/en/dev/packaging/misc/packaging_apps_git)
  - [Create a Development Environment with VirtualBox](https://doc.yunohost.org/en/dev/packaging/misc/packaging_apps_virtualbox)
  - [General Scope of Shell Variables](https://doc.yunohost.org/en/dev/packaging/misc/shell_variables_scope)
- **YunoHost Core Development (`doc.yunohost.org/en/dev/core/`)**
  - [Core Development Overview](https://doc.yunohost.org/en/dev/core/)
  - [YunoHost Architecture (`moulinette`, `yunohost`, `ssowat`, `yunohost-portal`, `yunohost-admin`)](https://doc.yunohost.org/en/dev/core/architecture)
  - [Development Environment (`ynh-dev` & Incus)](https://doc.yunohost.org/en/dev/core/devenv)
  - [Working on the API and CLI (`actionsmap`)](https://doc.yunohost.org/en/dev/core/ynh_core)
  - [Working on the YunoHost WebAdmin](https://doc.yunohost.org/en/dev/core/ynh_admin)
  - [Technical Details for Config Panel Structure & Form Option Types](https://doc.yunohost.org/en/dev/core/forms)
  - [How the Main Domain Is Used](https://doc.yunohost.org/en/dev/core/maindomain)

### Official YunoHost Repositories, Schemas & Tools
- **Template & Catalog**
  - [`YunoHost/example_ynh`](https://github.com/YunoHost/example_ynh) — Canonical Packaging v2 + Helpers v2.1 app template
  - [YunoHost App Generator](https://appgenerator.yunohost.org/) — Interactive web generator for new packages
  - [`YunoHost/apps`](https://github.com/YunoHost/apps) — Official app catalog (`apps.toml`, `categories.toml`, `antifeatures.toml`, `logos/`)
  - [`YunoHost-Apps` Organization](https://github.com/YunoHost-Apps) — Community-maintained app repositories
- **JSON Schemas**
  - [`manifest.v2.schema.json`](https://raw.githubusercontent.com/YunoHost/apps/main/schemas/manifest.v2.schema.json)
  - [`tests.v1.schema.json`](https://raw.githubusercontent.com/YunoHost/apps/main/schemas/tests.v1.schema.json)
  - [`config_panel.v1.schema.json`](https://raw.githubusercontent.com/YunoHost/apps/main/schemas/config_panel.v1.schema.json)
  - [`apps.toml.schema.json`](https://raw.githubusercontent.com/YunoHost/apps/main/schemas/apps.toml.schema.json)
- **Testing, Linting, CI & Automation**
  - [`YunoHost/package_linter`](https://github.com/YunoHost/package_linter) — Official static analyzer for `*_ynh` packages
  - [`YunoHost/package_check`](https://github.com/YunoHost/package_check) — Incus-based full lifecycle integration test runner
  - [`YunoHost/apps-tools`](https://github.com/YunoHost/apps-tools) — `autoupdate_app_sources.py`, `readme_generator`, and `packaging_v2` converter
  - [`YunoHost/ynh-dev`](https://github.com/YunoHost/ynh-dev) — Incus container development environment
  - [Official App CI (`ci-apps.yunohost.org`)](https://ci-apps.yunohost.org/ci/) & [Dev CI (`ci-apps-dev.yunohost.org`)](https://ci-apps-dev.yunohost.org/ci/)
  - [Packaging Dashboard (`apps.yunohost.org/dash`)](https://apps.yunohost.org/dash) & [Apps Catalog](https://apps.yunohost.org/)
- **Community & Copilot Plugin Docs**
  - [YunoHost App Packaging Chatroom (Matrix / XMPP)](https://doc.yunohost.org/en/community/chat_rooms) & [YunoHost Forum](https://forum.yunohost.org/)
  - [VS Code Agent Plugins Documentation](https://code.visualstudio.com/docs/copilot/customization/agent-plugins) & [Authoring Reference](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference)
  - [GitHub Copilot CLI Plugins Reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

---

## License

[MIT](./LICENSE)
