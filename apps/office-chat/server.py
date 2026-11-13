import argparse
import hmac
import json
import logging
import sqlite3
import threading
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
from uuid import UUID


class Chat:
    def __init__(self, database, users):
        self.database = database
        self.users = users
        self.changed = threading.Condition()
        self.presence_lock = threading.Lock()
        self.presence = {}
        with closing(self.connect()) as db, db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL, recipient TEXT NOT NULL,
                nonce TEXT NOT NULL, text TEXT NOT NULL,
                sent_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                archive TEXT NOT NULL DEFAULT 'pending', bitrix_id INTEGER,
                UNIQUE (sender, nonce))''')
            # A crash during an external write leaves its outcome unknown.
            db.execute("UPDATE messages SET archive='review' WHERE archive='sending'")

    def connect(self):
        db = sqlite3.connect(self.database)
        db.row_factory = sqlite3.Row
        return db

    def update_presence(self, user, status=None):
        with self.presence_lock:
            now = time.monotonic()
            _, previous = self.presence.get(user, (0, 'online'))
            self.presence[user] = now, status or previous
            return {key: value for key, (seen, value) in self.presence.items() if now - seen < 12}

    def messages(self, user, after=None):
        columns = 'id, sender, recipient, text, sent_at'
        with closing(self.connect()) as db:
            if after is None:
                rows = db.execute(f'''SELECT {columns} FROM messages
                    WHERE sender=? OR recipient=? ORDER BY id DESC LIMIT 200''', (user, user))
                return [dict(row) for row in reversed(list(rows))]
            rows = db.execute(f'''SELECT {columns} FROM messages
                WHERE id>? AND (sender=? OR recipient=?) ORDER BY id LIMIT 200''',
                              (after, user, user))
            return [dict(row) for row in rows]

    def receive(self, user, after):
        with self.changed:
            rows = self.messages(user, after)
            if rows:
                return rows
            return self.changed.wait_for(lambda: self.messages(user, after), timeout=15) or []

    def send(self, sender, body):
        recipient = str(body['recipient'])
        nonce = str(UUID(body['nonce']))
        text = body['text'].strip()
        if recipient == sender or recipient not in self.users or not 1 <= len(text) <= 4000:
            raise ValueError('Invalid recipient or message length')
        with self.changed, closing(self.connect()) as db:
            with db:
                db.execute('''INSERT INTO messages (sender, recipient, nonce, text)
                    VALUES (?, ?, ?, ?) ON CONFLICT(sender, nonce) DO NOTHING''',
                           (sender, recipient, nonce, text))
                row = db.execute('SELECT * FROM messages WHERE sender=? AND nonce=?',
                                 (sender, nonce)).fetchone()
                if row['recipient'] != recipient or row['text'] != text:
                    raise ValueError('Message ID is already in use')
            self.changed.notify_all()
        return row['id']

    def archive_one(self):
        enabled = [user for user, data in self.users.items() if data.get('bitrix_webhook')]
        if not enabled:
            return False
        placeholders = ','.join('?' for _ in enabled)
        with closing(self.connect()) as db:
            with db:
                row = db.execute(f'''SELECT * FROM messages WHERE archive='pending'
                    AND sender IN ({placeholders}) ORDER BY id LIMIT 1''', enabled).fetchone()
                if row is None:
                    return False
                db.execute("UPDATE messages SET archive='sending' WHERE id=?", (row['id'],))
            status, bitrix_id = self.write_bitrix(row)
            with db:
                db.execute('UPDATE messages SET archive=?, bitrix_id=? WHERE id=?',
                           (status, bitrix_id, row['id']))
        if status == 'review':
            logging.warning('Check Bitrix24 archive for local message %s', row['id'])
        return status != 'pending'

    def write_bitrix(self, row):
        webhook = self.users[row['sender']]['bitrix_webhook'].rstrip('/')
        request = Request(webhook + '/im.message.add', method='POST',
                          headers={'Content-Type': 'application/json'},
                          data=json.dumps({'DIALOG_ID': row['recipient'],
                                           'MESSAGE': row['text']}).encode())
        try:
            with urlopen(request, timeout=5) as response:
                result = json.load(response).get('result')
                if type(result) is int and result > 0:
                    return 'archived', result
        except HTTPError as error:
            with error:
                if error.code == 429:
                    return 'pending', None
                try:
                    if json.load(error).get('error') in {'QUERY_LIMIT_EXCEEDED', 'OPERATION_TIME_LIMIT'}:
                        return 'pending', None
                except (ValueError, AttributeError):
                    pass
        except URLError as error:
            if isinstance(error.reason, ConnectionRefusedError):
                return 'pending', None
        except (OSError, ValueError, AttributeError):
            pass
        # im.message.add has no documented idempotency key. Check ambiguous writes manually.
        return 'review', None

    def archive_forever(self, stop):
        while not stop.is_set():
            if not self.archive_one():
                stop.wait(3)


class Handler(BaseHTTPRequestHandler):
    timeout = 25

    def log_message(self, format, *args):
        pass

    def reply(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def authenticated_user(self):
        user = self.headers.get('X-User', '')
        data = self.server.chat.users.get(user)
        supplied = self.headers.get('Authorization', '').encode()
        if data and hmac.compare_digest(supplied, ('Bearer ' + data['token']).encode()):
            return user
        self.reply(401, {'error': 'Unauthorized'})
        return None

    def do_GET(self):
        user = self.authenticated_user()
        if user is None:
            return
        url = urlsplit(self.path)
        chat = self.server.chat
        if url.path == '/bootstrap':
            self.reply(200, {'users': {key: value['name'] for key, value in chat.users.items()},
                             'messages': chat.messages(user)})
        elif url.path == '/events':
            try:
                after = int(parse_qs(url.query)['after'][0])
                if not 0 <= after <= 2**63 - 1:
                    raise ValueError
            except (KeyError, ValueError):
                self.reply(400, {'error': 'Invalid cursor'})
                return
            self.reply(200, chat.receive(user, after))
        else:
            self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        user = self.authenticated_user()
        if user is None:
            return
        if self.path not in {'/messages', '/presence'}:
            self.reply(404, {'error': 'Not found'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 64 * 1024:
                raise ValueError
            body = json.loads(self.rfile.read(size))
            if self.path == '/presence':
                status = body['status']
                if status not in {'online', 'away', 'busy'}:
                    raise ValueError
                self.reply(200, self.server.chat.update_presence(user, status))
                return
            message_id = self.server.chat.send(user, body)
        except (ValueError, KeyError, TypeError, AttributeError):
            self.reply(400, {'error': 'Invalid message'})
            return
        self.reply(200, {'id': message_id})


class ChatServer(ThreadingHTTPServer):
    request_queue_size = 128


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    users = config['users']
    for user, data in users.items():
        if not user.isascii() or not user.isdecimal() or int(user) < 1 or not data['token']:
            parser.error('Each user requires a positive Bitrix24 ID and a token')
        webhook = data.get('bitrix_webhook')
        if webhook:
            url = urlsplit(webhook)
            parts = url.path.strip('/').split('/')
            if (url.scheme not in {'http', 'https'} or not url.hostname or url.query
                    or len(parts) != 3 or parts[:2] != ['rest', user] or not parts[2]):
                parser.error(f'Invalid Bitrix24 webhook for user {user}')
    logging.basicConfig(level=logging.INFO)
    chat = Chat(args.config.with_suffix('.sqlite3'), users)
    stop = threading.Event()
    with ChatServer((config.get('host', '127.0.0.1'), config.get('port', 8765)), Handler) as server:
        server.chat = chat
        threading.Thread(target=chat.archive_forever, args=(stop,), daemon=True).start()
        logging.info('Chat listening on %s:%s', *server.server_address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()


if __name__ == '__main__':
    main()
