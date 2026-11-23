# NGINX, Systemd, PHP-FPM, SSOwat & LDAP Integration Reference

Sources: `doc.yunohost.org/en/dev/packaging/advanced/sso_ldap_integration`, `example_ynh`, and `package_linter` (`tests/test_configurations.py`).

---

## 1. NGINX Configuration Rules (`conf/nginx.conf`)

Rendered to `/etc/nginx/conf.d/$domain.d/$app.conf` via `ynh_config_add_nginx`:
- `#sub_path_only` prefix is automatically uncommented when `$path != "/"`.
- `#root_path_only` prefix is automatically uncommented when `$path == "/"`.
- When `$path == "/"`, `__PATH__/` is automatically collapsed to `/` (preventing `//`).

### Mandatory `package_linter` Rules (YunoHost >= 12.1.38)
1. **Include YunoHost proxy/fastcgi param snippets**:
   - Reverse proxy with `integration.sso = true` -> `include proxy_params_with_auth;`
   - Reverse proxy with `integration.sso = false` or `"not_relevant"` -> `include proxy_params_no_auth;`
   - PHP-FPM with `integration.sso = true` -> `include fastcgi_params_with_auth;`
   - PHP-FPM with `integration.sso = false` or `"not_relevant"` -> `include fastcgi_params_no_auth;`
2. **Do NOT duplicate headers already set in `proxy_params_*` / `fastcgi_params_*`**:
   - Never manually set `Host`, `X-Real-IP`, `X-Scheme`, `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host`, `X-Forwarded-Scheme`, `X-Forwarded-Ssl`, `X-Forwarded-Server`, `Upgrade $http_upgrade`, `Connection $connection_upgrade`, `REMOTE_USER`, `PATH_INFO`, or `SCRIPT_FILENAME`.
3. **Never use `add_header` inside `location` blocks** (NGINX drops parent security headers when `add_header` is used in a child block):
   - Always use `more_set_headers "Header-Name: value";` (exact quoted `"Name: value";` syntax!).
4. **Prevent alias path-traversal vulnerability**:
   - Always pair `location __PATH__/ {` (trailing `/`) with `alias __INSTALL_DIR__/;` (trailing `/`), preceded by `#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;`.
5. **Regex locations**: Anchor with `^`, e.g. `location ~ ^__PATH__/api/`.
6. **No HTTP->HTTPS redirects**: Never write `if ($scheme = http)` (handled globally by YunoHost).
7. **Prefer `$host`** over `$http_host`.

### Reverse Proxy Pattern (`conf/nginx.conf`)
```nginx
#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;
location __PATH__/ {
  proxy_pass http://127.0.0.1:__PORT__/;
  include proxy_params_no_auth; # Use proxy_params_with_auth ONLY when integration.sso = true
  proxy_redirect off;
  # client_max_body_size 50M;
}
```
*(Note on trailing slash in `proxy_pass`: `proxy_pass http://127.0.0.1:__PORT__/;` strips `__PATH__` before forwarding to upstream; `proxy_pass http://127.0.0.1:__PORT__;` forwards the full `__PATH__/...` URI when the upstream app itself is configured with `BASE_URL=__PATH__`.)*

### PHP-FPM Pattern (`conf/nginx.conf`)
```nginx
#sub_path_only rewrite ^__PATH__$ __PATH__/ permanent;
location __PATH__/ {
  alias __INSTALL_DIR__/;
  index index.php;
  # client_max_body_size 50M;

  try_files $uri $uri/ __PATH__/index.php?$args;
  location ~ [^/]\.php(/|$) {
    fastcgi_pass unix:/var/run/php/php__PHP_VERSION__-fpm-__APP__.sock;
    include fastcgi_params_no_auth; # Use fastcgi_params_with_auth when integration.sso = true
  }
}
```

---

## 2. Systemd Service & Hardening Rules (`conf/systemd.service`)

1. **Dedicated User**: Always run as `User=__APP__` and `Group=__APP__` (never `root` or `www-data`).
2. **Loopback Binding**: Configure the app daemon to listen on `127.0.0.1:__PORT__` (not `0.0.0.0` or `::`), preventing direct port bypass of NGINX/SSOwat.
3. **Never Put Secrets in `Environment=`**: `package_linter` flags any `Environment=` line matching `pass|secret|key` as an **Error** because unit files in `/etc/systemd/system/` are world-readable (`644`). Put secrets in `EnvironmentFile=__INSTALL_DIR__/.env` (rendered via `ynh_config_add` with `chmod 400` or `600`, `chown "$app:$app"`).
4. **Runtime PATH for Node.js / Ruby / Go**:
   - Node.js (`[resources.nodejs]`): `Environment="PATH=__PATH_WITH_NODEJS__"` and/or `ExecStart=__NODEJS_DIR__/node ...`
   - Ruby (`[resources.ruby]`): `Environment="PATH=__PATH_WITH_RUBY__"` and/or `ExecStart=__RUBY_DIR__/bundle ...`
   - Go (`[resources.go]`): Build binary during `install`/`upgrade` with `ynh_exec_as_app go build ...` and run `__INSTALL_DIR__/myapp` directly in `ExecStart=`.
5. **Sandboxing Baseline**: Include the standard `NoNewPrivileges=yes`, `PrivateTmp=yes`, `ProtectSystem=full` (or `strict` with `ReadWritePaths=__INSTALL_DIR__ __DATA_DIR__ /var/log/__APP__`), `CapabilityBoundingSet=~...`, and `SystemCallFilter=~...` directives from `./assets/systemd.service`. (Note: Node.js/V8/Java JIT apps only fail if `MemoryDenyWriteExecute=yes` is added—it is intentionally omitted from the standard baseline.)
6. **YunoHost Service Registration**:
   Call identically in `scripts/install`, `scripts/upgrade`, and `scripts/restore`:
   ```bash
   yunohost service add "$app" --description="Short description of $app" --log="/var/log/$app/$app.log"
   ```
   (Omit `--log=...` if logging strictly to systemd journal via `StandardOutput=journal`; never pass `--needs_exposed_ports` for internal reverse-proxied HTTP ports!)

---

## 3. SSOwat HTTP Headers, Basic Auth & Logout

### Injected Headers (when `auth_header = true` on the permission & `*_params_with_auth` in NGINX)
| Upstream HTTP Header | PHP `$_SERVER` Key | Spoof-Protected | Content |
|---|---|---|---|
| `YNH_USER` | `HTTP_YNH_USER` | **Yes** | Authenticated YunoHost username (`uid`) |
| `YNH_USER_EMAIL` | `HTTP_YNH_USER_EMAIL` | **Yes** | Primary email (`mail`) |
| `YNH_USER_FULLNAME` | `HTTP_YNH_USER_FULLNAME` | **Yes** | Full display name (`displayname`) |
| `REMOTE_USER` | `REMOTE_USER` / `HTTP_REMOTE_USER` | **Yes** (via `*_params_with_auth`) | Authenticated username |
| `Authorization` (`Basic ...`) | `HTTP_AUTHORIZATION` | **No** (if passthrough enabled) | Client credentials; app must validate password |

### Apps With External Basic-Auth / Bearer Token Clients (WebDAV, CalDAV, CardDAV, Mobile APIs)
- **Bearer Token APIs**: If mobile/CLI clients send `Authorization: Bearer <token>` to `/api`, either set `api.url = "/api"` + `api.auth_header = false` in `[resources.permissions]` OR use `proxy_params_no_auth` on the API location so SSOwat does not overwrite `Authorization`.
- **Direct HTTP Basic Auth Clients** (Nextcloud, SOGo, Baikal): Disable SSOwat Basic-Auth spoofing protection in `scripts/install` and `scripts/upgrade`:
  ```bash
  ynh_app_setting_set --key=protect_against_basic_auth_spoofing --value=false
  ```
- **SSOwat Logout URL**: `https://__DOMAIN__/yunohost/sso/?action=logout`

---

## 4. YunoHost LDAP Directory Schema (`integration.ldap = true`)

YunoHost runs OpenLDAP (`slapd`) locally on `127.0.0.1:389` (anonymous read bind allowed, no TLS required on loopback):

| Setting | Value |
|---|---|
| Host / URI | `127.0.0.1` / `ldap://127.0.0.1:389` |
| Port | `389` (StartTLS/LDAPS not needed on `127.0.0.1`) |
| Bind DN / Password | Anonymous bind (leave empty) |
| Base DN | `dc=yunohost,dc=org` |
| Users Base DN | `ou=users,dc=yunohost,dc=org` |
| Permissions Base DN | `ou=permission,dc=yunohost,dc=org` |
| User Filter (with app permission check!) | `(&(|(objectclass=posixAccount))(uid=%s)(permission=cn=__APP__.main,ou=permission,dc=yunohost,dc=org))` *(replace `%s` / `%uid` / `{username}` per app syntax)* |
| Admin Group Filter (optional) | `(&(objectclass=posixGroup)(cn=admins)(memberUid=%s))` or permission `cn=__APP__.admin,ou=permission,dc=yunohost,dc=org` |
| Username Attribute | `uid` |
| Full Name Attribute | `displayname` (or `cn`) |
| First / Last Name | `givenName` / `sn` |
| Email Attribute | `mail` |

### OIDC-Only Upstream Applications
YunoHost Core / SSOwat is **not** a native OIDC provider. If an upstream app *only* supports OIDC (no LDAP and no trusted HTTP header auth), set `ldap = false` and `sso = false` in `manifest.toml`, and document in `doc/ADMIN.md` how admins can optionally connect it to a YunoHost-packaged OIDC IdP (`dex_ynh`, `authelia_ynh`, `authentik_ynh`, `keycloak_ynh`, or `pocket-id_ynh`).
