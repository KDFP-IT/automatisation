#!/usr/bin/env python3
"""KDFP portal auth: login via local pair or LDAP/AD bind, cookie sessions.

Endpoints (all JSON):
  GET  /auth/mode                   -> {"mode", "domain"}
  POST /auth/login   {login, password} -> 200 {user, tools:[ids], admin} + cookie
  POST /auth/logout                 -> 200, clears cookie
  GET  /auth/me                     -> 200 {user, tools, admin} | 401
  GET  /auth/check?tool=<id>        -> 200 (+X-Auth-User) | 401 | 403

Sessions are stateless HMAC-signed cookies: no server storage, restarts safe.
In ldap mode login does a direct user bind (UPN) plus group checks through
LDAP_MATCHING_RULE_IN_CHAIN, so no service account is needed. /auth/check
never touches LDAP: users logged in before an AD outage keep working, only
new logins fail (503).
"""

import base64
from email.header import Header
import hashlib
import hmac
import json
import os
import ssl
import sys
import time
import tomllib
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

COOKIE_NAME = "kdfp_auth"
BODY_LIMIT = 8 * 1024
FAIL_WINDOW_S = 300
FAIL_MAX = 5
IN_CHAIN = "1.2.840.113556.1.4.1941"


def display_header(value: str) -> str:
    """Encode a display name for an HTTP header (RFC 2047).

    stdlib http.server send_header() only speaks latin-1: a raw Cyrillic
    displayName raises UnicodeEncodeError, drops the auth_request
    subrequest connection and nginx answers 500 to every gated tool
    request. ASCII names go through byte-identical to before; only
    non-latin-1 names are encoded.
    """
    value = value or ""
    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        return Header(value, "utf-8").encode()


def env(name, default=""):
    return os.environ.get(name, default)


def fail(msg):
    print(f"auth: FATAL: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


SESSION_SECRET = env("SESSION_SECRET")
if not SESSION_SECRET:
    fail("SESSION_SECRET is empty (generate: openssl rand -hex 32)")
SESSION_TTL = int(env("SESSION_TTL_H", "12")) * 3600
COOKIE_SECURE = env("COOKIE_SECURE", "1") == "1"
AUTH_MODE = env("AUTH_MODE", "local").strip().lower()
if AUTH_MODE not in ("local", "ldap"):
    fail(f"AUTH_MODE must be local|ldap, got {AUTH_MODE!r}")

with open(env("ACCESS_FILE", "/etc/auth/access.toml"), "rb") as fh:
    ACCESS = tomllib.load(fh)
BASE_GROUP = ACCESS.get("base_group", "")
ADMIN_GROUPS = list(ACCESS.get("admin_groups", []))
TOOLS = ACCESS.get("tools", {})
AUTH_OPEN = env("AUTH_OPEN", "0") == "1"
if AUTH_MODE == "ldap" and not BASE_GROUP and not AUTH_OPEN:
    fail("base_group is required in access.toml for ldap mode (or set AUTH_OPEN=1)")

LDAP_URL = env("LDAP_URL")
LDAP_TLS_MODE = env("LDAP_TLS_MODE", "").strip().lower()
LDAP_BASE_DN = env("LDAP_BASE_DN")
LDAP_DOMAIN = env("LDAP_DOMAIN")
LDAP_CA_FILE = env("LDAP_CA_FILE")
LDAP_TIMEOUT = int(env("LDAP_TIMEOUT_S", "5"))
if AUTH_MODE == "ldap" and not (LDAP_URL and LDAP_BASE_DN and LDAP_DOMAIN):
    fail("LDAP_URL, LDAP_BASE_DN and LDAP_DOMAIN are required in ldap mode")

LOCAL_LOGIN = env("LOCAL_LOGIN")
LOCAL_PASSWORD = env("LOCAL_PASSWORD")
if AUTH_MODE == "local" and not (LOCAL_LOGIN and LOCAL_PASSWORD):
    fail("LOCAL_LOGIN and LOCAL_PASSWORD are required in local mode")

_fails: dict[str, list[float]] = {}


def throttled(login: str) -> bool:
    now = time.time()
    hits = [t for t in _fails.get(login, []) if now - t < FAIL_WINDOW_S]
    _fails[login] = hits
    return len(hits) >= FAIL_MAX


def note_fail(login: str) -> None:
    _fails.setdefault(login, []).append(time.time())


def sign(payload: bytes) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def mint(user: str, tools: list[str], admin: bool, display_name: str = "") -> str:
    body = {"u": user, "t": sorted(tools), "a": admin, "n": display_name,
            "exp": int(time.time()) + SESSION_TTL}
    raw = base64.urlsafe_b64encode(json.dumps(body).encode()).decode()
    return f"{raw}.{sign(raw.encode())}"


def verify(token: str) -> dict | None:
    try:
        raw, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, sign(raw.encode())):
            return None
        body = json.loads(base64.urlsafe_b64decode(raw.encode()))
        if int(body.get("exp", 0)) < time.time():
            return None
        return body
    except (ValueError, KeyError):
        return None


def ldap_check_groups(upn: str, password: str) -> tuple[str, str, set[str]]:
    from ldap3 import Server, Connection, Tls
    from ldap3.core.exceptions import LDAPException
    from ldap3.core.results import RESULT_INVALID_CREDENTIALS
    from ldap3.utils.conv import escape_filter_chars
    parsed = urlparse(LDAP_URL)
    scheme = parsed.scheme.lower()
    host, port = parsed.hostname or "", parsed.port or 0
    if scheme == "ldaps":
        if LDAP_TLS_MODE and LDAP_TLS_MODE != "ldaps":
            raise ConnectionError("LDAP_TLS_MODE conflicts with ldaps://")
        use_ssl, starttls = True, False
    elif scheme == "ldap":
        if LDAP_TLS_MODE == "none":
            use_ssl, starttls = False, False
        elif LDAP_TLS_MODE in ("", "starttls"):
            use_ssl, starttls = False, True
        else:
            raise ConnectionError(f"bad LDAP_TLS_MODE {LDAP_TLS_MODE!r}")
    else:
        raise ConnectionError(f"LDAP_URL scheme must be ldap(s), got {scheme!r}")

    tls = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLS_CLIENT,
              ca_certs_file=LDAP_CA_FILE or None)
    try:
        server = Server(host, port=port or None, use_ssl=use_ssl, tls=tls,
                        connect_timeout=LDAP_TIMEOUT)
        conn = Connection(server, user=upn, password=password,
                          receive_timeout=LDAP_TIMEOUT,
                          raise_exceptions=True)
        conn.open()
        if starttls:
            conn.start_tls()
        try:
            bound = conn.bind()
        except LDAPException as problem:
            if "invalidCredentials" in str(problem):
                raise KeyError("bad credentials")
            raise ConnectionError(f"bind failed: {problem}") from problem
        if not bound:
            result = conn.result or {}
            if result.get("result") == RESULT_INVALID_CREDENTIALS:
                raise KeyError("bad credentials")
            raise ConnectionError(f"bind failed: {result.get('description')}")
    except KeyError:
        raise
    except LDAPException as problem:
        raise ConnectionError(f"ad unreachable: {problem}") from problem

    try:
        wanted = sorted({BASE_GROUP, *ADMIN_GROUPS,
                         *(g for spec in TOOLS.values() for g in spec.get("groups", []))})
        conn.search(LDAP_BASE_DN, f"(userPrincipalName={escape_filter_chars(upn)})",
                    attributes=["distinguishedName", "displayName"])
        if not conn.entries:
            raise KeyError("no such user")
        user_dn = str(conn.entries[0].distinguishedName)
        display_name = str(conn.entries[0].displayName or "")
        if AUTH_OPEN:
            return user_dn, display_name, set()
        matched = set()
        for group_dn in wanted:
            conn.search(group_dn, f"(member:{IN_CHAIN}:={escape_filter_chars(user_dn)})",
                        search_scope="BASE", attributes=["cn"])
            if conn.entries:
                matched.add(group_dn)
        return user_dn, display_name, matched
    except KeyError:
        raise
    except LDAPException as problem:
        raise ConnectionError(f"ad search failed: {problem}") from problem
    finally:
        conn.unbind()


def allowed_tools(matched: set[str]) -> tuple[list[str], bool]:
    admin = bool(matched & set(ADMIN_GROUPS))
    if admin:
        return sorted(TOOLS), True
    return sorted(tid for tid, spec in TOOLS.items()
                  if matched & set(spec.get("groups", []))), False


class Handler(BaseHTTPRequestHandler):
    server_version = "kdfp-auth/1"
    def log_message(self, format, *args):  # noqa: A002 - stdlib signature
        pass

    def _send(self, code: int, obj: dict, headers: dict | None = None,
              cookie: str | None = None):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _cookie(self) -> str:
        jar = SimpleCookie(self.headers.get("Cookie", ""))
        return jar[COOKIE_NAME].value if COOKIE_NAME in jar else ""

    def _session(self) -> dict | None:
        token = self._cookie()
        return verify(token) if token else None

    def _set_cookie(self, token: str) -> str:
        parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly",
                 "SameSite=Lax", f"Max-Age={SESSION_TTL}"]
        if COOKIE_SECURE:
            parts.append("Secure")
        return "; ".join(parts)

    def _clear_cookie(self) -> str:
        parts = [f"{COOKIE_NAME}=expired", "Path=/", "HttpOnly",
                 "SameSite=Lax", "Max-Age=0"]
        if COOKIE_SECURE:
            parts.append("Secure")
        return "; ".join(parts)

    def do_GET(self):
        target = urlparse(self.path)
        if target.path == "/auth/mode":
            self._send(200, {"mode": AUTH_MODE, "domain": LDAP_DOMAIN or None})
        elif target.path == "/auth/me":
            session = self._session()
            if not session:
                self._send(401, {"error": "unauthorized", "mode": AUTH_MODE})
                return
            self._send(200, {"user": session["u"], "tools": session["t"],
                             "admin": session["a"], "display_name": session.get("n", "")})
        elif target.path == "/auth/check":
            session = self._session()
            if not session:
                self._send(401, {"error": "unauthorized"})
                return
            tool = parse_qs(target.query).get("tool", [""])[0]
            if not tool or tool in session["t"] or session["a"]:
                self._send(200, {"ok": True},
                           {"X-Auth-User": session["u"],
                            "X-Auth-Name": display_header(session.get("n", ""))})
            else:
                self._send(403, {"error": "forbidden", "tool": tool})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path == "/auth/login":
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length > BODY_LIMIT:
                self._send(413, {"error": "body_too_large"})
                return
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                self._send(400, {"error": "bad_json"})
                return
            login = str(data.get("login", "")).strip()
            password = str(data.get("password", ""))
            if not login or not password:
                self._send(400, {"error": "login_and_password_required"})
                return
            if throttled(login):
                self._send(429, {"error": "too_many_attempts"})
                return
            try:
                if AUTH_MODE == "local":
                    if not (hmac.compare_digest(login, LOCAL_LOGIN)
                            and hmac.compare_digest(password, LOCAL_PASSWORD)):
                        raise KeyError("bad credentials")
                    tools = sorted(TOOLS)
                    admin, user, display_name = True, login, login
                else:
                    upn = login if "@" in login else f"{login}@{LDAP_DOMAIN}"
                    _, display_name, matched = ldap_check_groups(upn, password)
                    if AUTH_OPEN:
                        tools, admin = sorted(TOOLS), False
                    else:
                        if BASE_GROUP not in matched:
                            self._send(403, {"error": "no_portal_access"})
                            print(f"auth: login {login}: no base group", flush=True)
                            return
                        tools, admin = allowed_tools(matched)
                    user = upn
                print(f"auth: login {login}: ok admin={admin} tools={len(tools)}",
                      flush=True)
                self._send(200, {"user": user, "tools": tools, "admin": admin,
                                 "display_name": display_name},
                           cookie=self._set_cookie(mint(user, tools, admin, display_name)))
            except KeyError:
                note_fail(login)
                print(f"auth: login {login}: bad credentials", flush=True)
                self._send(401, {"error": "bad_credentials"})
            except ConnectionError as problem:
                print(f"auth: login {login}: {problem}", flush=True)
                self._send(503, {"error": "ad_unreachable"})
        elif self.path == "/auth/logout":
            self._send(200, {"ok": True}, cookie=self._clear_cookie())
        else:
            self._send(404, {"error": "not_found"})


if __name__ == "__main__":
    port = int(env("PORT", "8080"))
    print(f"auth: mode={AUTH_MODE} port={port} tools={sorted(TOOLS)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
