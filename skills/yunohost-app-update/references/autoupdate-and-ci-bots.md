# Automated Source Updates (`autoupdate`), Branches & CI Bot Commands

Sources: `doc.yunohost.org/en/dev/packaging/resources`, `advanced/advanced_packagers`, `YunoHost/apps-tools`, and `YunoHost/yunorunner`.

---

## 1. `[resources.sources.<id>.autoupdate]` Complete Reference

Executed daily by `YunoHost/apps-tools/autoupdate_app_sources/autoupdate_app_sources.py` across `YunoHost-Apps` repositories, automatically opening `ci-auto-update-*` PRs and triggering `package_check` CI!

### All 13 Valid `autoupdate.strategy` Values
- **GitHub**: `latest_github_release`, `latest_github_tag`, `latest_github_commit`
- **GitLab** (gitlab.com or self-hosted GitLab): `latest_gitlab_release`, `latest_gitlab_tag`, `latest_gitlab_commit`
- **Gitea**: `latest_gitea_release`, `latest_gitea_tag`, `latest_gitea_commit`
- **Forgejo**: `latest_forgejo_release`, `latest_forgejo_tag`, `latest_forgejo_commit`
- **Webpage link scraping**: `latest_webpage_link` *(note: supported in `autoupdate_app_sources.py`, though `manifest.v2.schema.json` strictly enums the 12 forge strategies above)*

### Strategy Selection Guide
1. **`latest_<forge>_release`** *(Preferred whenever upstream publishes Releases)*:
   - Only strategy that includes upstream release notes/changelog links in automated PRs.
   - Required whenever downloading compiled release assets (`autoupdate.asset`) instead of source tarballs.
   - Skips drafts and pre-releases automatically (unless `allow_prereleases = true`).
2. **`latest_<forge>_tag`**:
   - Uses source code tag archive tarballs (`refs/tags/...`).
   - Semantically sorts `x.y.z` / `vx.y.z` tags and ignores `alpha`, `beta`, `rc`, `start`.
3. **`latest_<forge>_commit`**:
   - Pulls latest commit tarball from default branch (or `autoupdate.branch`), setting `version` to `YYYY.MM.DD~ynh1` (or `force_version` strftime pattern).

### Examples

```toml
# 1. Source tarball from GitHub tags (uses [upstream].code automatically):
[resources.sources.main]
url = "https://github.com/org/myapp/archive/refs/tags/v2.4.0.tar.gz"
sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
autoupdate.strategy = "latest_github_tag"

# 2. Multi-arch release binaries with custom tag prefix regex:
[resources.sources.main]
in_subdir = false
amd64.url = "https://github.com/org/myapp/releases/download/release-2.4.0/myapp-linux-x86_64.tar.gz"
amd64.sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
arm64.url = "https://github.com/org/myapp/releases/download/release-2.4.0/myapp-linux-arm64.tar.gz"
arm64.sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
autoupdate.strategy = "latest_github_release"
autoupdate.version_regex = '^release-(.*)$'
autoupdate.asset.amd64 = '^myapp-linux-x86_64\.tar\.gz$'
autoupdate.asset.arm64 = '^myapp-linux-arm64\.tar\.gz$'

# 3. Secondary plugin/asset from a different upstream repo:
[resources.sources.plugin]
url = "https://github.com/other/plugin/releases/download/v1.1.0/plugin.zip"
sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
autoupdate.strategy = "latest_github_release"
autoupdate.upstream = "https://github.com/other/plugin"
autoupdate.asset = '^plugin\.zip$'
```
*(Note: Use single quotes `'...'` in TOML for regexes so `\.` does not need double escaping! When `main` updates, version becomes `<new_ver>~ynh1`; when only a secondary source updates, `~ynhN` increments to `~ynh(N+1)`.)*

---

## 2. `YunoHost-Apps` Git Branch Workflow

- **`main` (or `master`)**: Live branch served directly to all YunoHost users via `apps.toml`! Never push untested changes directly to `main`. Merging to `main` triggers Official CI (`https://ci-apps.yunohost.org/ci`).
- **`testing`**: Staging branch for PRs and manual testing (`sudo yunohost app install https://github.com/YunoHost-Apps/<app>_ynh/tree/testing`). When `testing` is merged into `main`, `yunohost-bot` automatically fast-forwards `testing` if behind.
- **`ci-auto-update-*`**: Auto-created PR branches targeting `testing` (or `main` if `testing` does not exist).

---

## 3. Pull Request Bot Commands (`YunoHost-Apps` & `YunoHost/apps`)

Comment any of these on an open PR (requires `YunoHost-Apps` org membership):

| PR Comment | Action |
|---|---|
| `!testme` *(or `!gogogadgetoci`)* | Schedules a full `package_check` CI run on `ci-apps-dev.yunohost.org` and posts live status badge + result summary |
| `!bump` *(or `!new_revision`)* | Increments `~ynhN` -> `~ynh(N+1)` in `manifest.toml`, regenerates `README.md`, and commits to PR |
| `!changelog <markdown>` *(or `!pre_upgrade <markdown>`)* | Appends `<markdown>` to `doc/PRE_UPGRADE.d/<manifest_version>.md` and commits to PR |
| `no_readme` *(in commit message)* | Prevents `yunohost-bot` from auto-regenerating `README.md` on that push |
