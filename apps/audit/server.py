#!/usr/bin/env python3
"""KDFP audit sink: single events table + editable saved-minutes norms.

Endpoints (JSON):
  POST /audit/event  {tool, action, [user], [duration_ms], [pages],
                      [status], [error], [details], [saved_minutes]}
                     -> 201 {id, saved_minutes}. User identity comes from the
                     X-Auth-User header injected by the portal nginx (its
                     auth_request already verified the session); an explicit
                     body user is accepted only for server-to-server calls
                     inside the docker network (tools reporting background
                     jobs). Header wins when both are present.
  GET  /audit/norms  -> [{tool, action, minutes}] (nginx gates to admins)
  PUT  /audit/norms  {tool, action, minutes} (nginx gates to admins)

Storage is one SQLite file on a persistent volume: restarts are safe, and
Metabase reads the same file (see deploy/metabase wiring in slice 4).
"""

import json
import os
import sqlite3
from datetime import datetime, UTC
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from email.header import decode_header, make_header

BODY_LIMIT = 64 * 1024
DB_PATH = os.environ.get("AUDIT_DB_PATH", "/data/audit.sqlite3")
PORT = int(os.environ.get("PORT", "8080"))


def auth_display_name(value):
    """Decode the RFC 2047 X-Auth-Name header set by portal auth.

    Plain ASCII values (old auth) pass through unchanged; decoding never
    raises — display-only data for events.
    """
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return value or ""

SEED_NORMS = [
    # (tool, action, minutes of manual work saved per action — estimates)
    ("kac", "build", 60.0),
    ("kac", "download", 2.0),
    ("bookmarks", "process", 15.0),
    ("bookmarks", "download", 2.0),
    ("trench", "project_create", 5.0),
    ("trench", "scheme_create", 10.0),
    ("trench", "scheme_save", 10.0),
    ("trench", "state_change", 2.0),
    ("signatures", "check", 20.0),
    ("signatures", "export", 2.0),
]


def now():
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          user_id TEXT NOT NULL,
          ad_login TEXT NOT NULL,
          user_name TEXT NOT NULL DEFAULT '',
          tool TEXT NOT NULL,
          action TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'ok',
          pages INTEGER,
          duration_ms INTEGER,
          saved_minutes REAL NOT NULL DEFAULT 0,
          error TEXT,
          details TEXT
        );
        CREATE INDEX IF NOT EXISTS events_tool_ts ON events(tool, ts);
        CREATE INDEX IF NOT EXISTS events_user_ts ON events(user_id, ts);
        CREATE TABLE IF NOT EXISTS norms(
          tool TEXT NOT NULL,
          action TEXT NOT NULL,
          minutes REAL NOT NULL,
          updated_at TEXT NOT NULL,
          PRIMARY KEY (tool, action)
        );
        """)
        cols = {row["name"] for row in db.execute("PRAGMA table_info(events)")}
        if "user_name" not in cols:
            db.execute("ALTER TABLE events ADD COLUMN user_name TEXT NOT NULL DEFAULT ''")
        stamp = now()
        db.executemany(
            "INSERT INTO norms(tool, action, minutes, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(tool, action) DO NOTHING",
            [(tool, action, minutes, stamp) for tool, action, minutes in SEED_NORMS],
        )


def lookup_minutes(tool, action):
    with connect() as db:
        row = db.execute(
            "SELECT minutes FROM norms WHERE tool=? AND action=?", (tool, action)
        ).fetchone()
        return float(row["minutes"]) if row else 0.0


class Handler(BaseHTTPRequestHandler):
    server_version = "kdfp-audit/1"
    def log_message(self, format, *args):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError:
            return None
        if length > BODY_LIMIT:
            return None
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return None

    def do_GET(self):
        if self.path == "/audit/norms":
            with connect() as db:
                rows = db.execute(
                    "SELECT tool, action, minutes FROM norms ORDER BY tool, action"
                ).fetchall()
            self._send(200, {"norms": [dict(row) for row in rows]})
        elif self.path == "/audit/health":
            with connect() as db:
                db.execute("SELECT 1").fetchone()
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/audit/event":
            self._send(404, {"error": "not_found"})
            return
        data = self._read_json()
        if data is None:
            self._send(400, {"error": "bad_json"})
            return
        user = (self.headers.get("X-Auth-User") or "").strip() \
            or str(data.get("user") or data.get("ad_login") or "").strip()
        user_name = auth_display_name(self.headers.get("X-Auth-Name")).strip() \
            or str(data.get("user_name") or "").strip()
        tool = str(data.get("tool") or "").strip()
        action = str(data.get("action") or "").strip()
        if not user or not tool or not action:
            self._send(400, {"error": "user_tool_action_required"})
            return
        ad_login = user.split("@")[0]
        if not user_name:
            user_name = ad_login
        try:
            minutes = data.get("saved_minutes")
            saved = float(minutes) if minutes is not None else lookup_minutes(tool, action)
        except (TypeError, ValueError):
            self._send(400, {"error": "bad_saved_minutes"})
            return
        details = data.get("details")
        try:
            details_json = json.dumps(details, ensure_ascii=False)[:4000] \
                if details is not None else None
        except (TypeError, ValueError):
            details_json = None
        with connect() as db:
            cursor = db.execute(
                "INSERT INTO events(ts, user_id, ad_login, user_name, tool, action, status,"
                " pages, duration_ms, saved_minutes, error, details)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (now(), user, ad_login, user_name[:180], tool[:64], action[:64],
                 str(data.get("status") or "ok")[:32],
                 data.get("pages"), data.get("duration_ms"), saved,
                 str(data.get("error") or "")[:1000] or None, details_json),
            )
            event_id = cursor.lastrowid
        self._send(201, {"id": event_id, "saved_minutes": saved})

    def do_PUT(self):
        if self.path != "/audit/norms":
            self._send(404, {"error": "not_found"})
            return
        data = self._read_json()
        if data is None:
            self._send(400, {"error": "bad_json"})
            return
        tool = str(data.get("tool") or "").strip()
        action = str(data.get("action") or "").strip()
        try:
            minutes = float(data.get("minutes"))
            if not (0 <= minutes <= 10080):
                raise ValueError()
        except (TypeError, ValueError):
            self._send(400, {"error": "bad_minutes"})
            return
        if not tool or not action:
            self._send(400, {"error": "tool_action_required"})
            return
        with connect() as db:
            db.execute(
                "INSERT INTO norms(tool, action, minutes, updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(tool, action) DO UPDATE SET minutes=excluded.minutes,"
                " updated_at=excluded.updated_at",
                (tool[:64], action[:64], minutes, now()),
            )
        self._send(200, {"tool": tool, "action": action, "minutes": minutes})


if __name__ == "__main__":
    init_db()
    print(f"audit: db={DB_PATH} port={PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
