"""Shared project catalogue, independent schemes, optimistic saves, SQLite persistence."""
import hashlib
import json
import math
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, abort, has_request_context
from werkzeug.exceptions import HTTPException


def now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

AUDIT_URL = os.environ.get("AUDIT_URL", "http://audit:8080")

def audit_event(action, user, status="ok", **fields):
    """Fire-and-forget audit event; never breaks the request on failure."""
    if not user:
        return
    if "user_name" not in fields and has_request_context():
        fields["user_name"] = request.headers.get("X-Auth-Name", "")
    try:
        payload = json.dumps({"tool": "trench", "action": action, "user": user,
                              "status": status, **fields}).encode()
        urlopen(Request(AUDIT_URL + "/audit/event", data=payload,
                        headers={"Content-Type": "application/json"}, method="POST"),
                timeout=2).close()
    except Exception:
        print(f"trench audit event {action} lost", flush=True)


def name(value, fallback=None):
    value = value if value is not None else fallback
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 180:
        raise ValueError('Название должно содержать от 1 до 180 символов.')
    return value.strip()


def validate_model(model):
    if not isinstance(model, dict) or model.get('version') not in (3, 4):
        raise ValueError('Ожидается модель схемы версии 3.')
    for key, limit in [('wells', 150), ('edges', 200), ('soils', 40)]:
        if not isinstance(model.get(key), list) or len(model[key]) > limit:
            raise ValueError('Некорректный список: ' + key)
    name(model.get('name'))
    if not isinstance(model.get('id'), str) or not 1 <= len(model['id']) <= 150: raise ValueError('Некорректный ID модели.')
    if not isinstance(model.get('notes', ''), str) or len(model.get('notes', '')) > 50000:
        raise ValueError('Некорректные исходные данные.')
    def objects(value):
        if not isinstance(value, dict): raise ValueError('Ожидается объект параметров.')
        for child in value.values():
            if isinstance(child, list):
                for item in child: objects(item)
            elif isinstance(child, dict): objects(child)
    objects(model)
    ids = set()

    def identifier(value):
        if not isinstance(value, str) or not value or len(value) > 150 or value in ids:
            raise ValueError('Некорректный или повторяющийся ID.')
        ids.add(value)

    def number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 1e8:
            raise ValueError('Некорректное числовое значение.')

    soils = set()
    for soil in model['soils']:
        identifier(soil.get('id')); soils.add(soil['id'])
        if not isinstance(soil.get('name'), str) or len(soil['name']) > 500:
            raise ValueError('Некорректное название грунта.')
        import re
        if not isinstance(soil.get('color'), str) or not re.fullmatch(r'#[a-fA-F0-9]{6}', soil['color']) or soil.get('group') not in ['I', 'II', 'III', 'IV', 'V', 'VI']:
            raise ValueError('Некорректный справочник грунтов.')
    def backfill_settings(obj):
        if obj.get('backfillSource', 'excavated') not in ['excavated', 'imported']:
            raise ValueError('Выберите материал засыпки.')
        if 'backfillMaterial' in obj and (not isinstance(obj['backfillMaterial'], str) or not obj['backfillMaterial'].strip() or len(obj['backfillMaterial']) > 180):
            raise ValueError('Укажите материал засыпки.')

    wells = {}
    for well in model['wells']:
        backfill_settings(well)
        if 'workingHeightOverride' in well:
            number(well['workingHeightOverride'])
            if well['workingHeightOverride'] <= 0: raise ValueError('Рабочая часть должна быть больше нуля.')
        identifier(well.get('id')); name(well.get('name'))
        for key in ['height', 'rotation', 'zeroAngle']:
            if key in well: number(well[key])
        for key, allowed in [('kind', ['well', 'endpoint']), ('heightMode', ['total', 'parts']), ('rotationMode', ['manual', 'pipe'])]:
            if key in well and well[key] not in allowed: raise ValueError('Некорректный режим узла.')
        if 'rotationEdge' in well and (not isinstance(well['rotationEdge'], str) or len(well['rotationEdge']) > 150): raise ValueError('Некорректная опорная труба.')
        for key in ['x', 'y', 'ground', 'diameter', 'width', 'length', 'wall', 'workingHeight', 'neckHeight', 'neckDiameter', 'neckWall', 'neckX', 'neckY', 'slab', 'base', 'baseProjection', 'pitMargin', 'pitSlope', 'pad', 'padMargin']:
            number(well.get(key))
        if well.get('shape') not in ['round', 'rect']:
            raise ValueError('Некорректная форма колодца.')
        if not isinstance(well.get('ports'), list) or len(well['ports']) > 40:
            raise ValueError('Некорректные подключения.')
        ports = set()
        for port in well['ports']:
            identifier(port.get('id')); number(port.get('invert')); ports.add(port['id'])
            if 'wall' in port and (isinstance(port['wall'], bool) or not isinstance(port['wall'], int) or not 0 <= port['wall'] <= 3): raise ValueError('Некорректная стена подключения.')
            if port.get('bearing') is not None: number(port['bearing'])
        wells[well['id']] = ports
        layers(well.get('layers'), soils, ['bottom'], number)
    used_ports = set()
    for edge in model['edges']:
        backfill_settings(edge)
        identifier(edge.get('id')); name(edge.get('name'))
        for end in ['from', 'to']:
            value = edge.get(end)
            if not isinstance(value, dict) or not isinstance(value.get('well'), str) or not isinstance(value.get('port'), str) or value.get('well') not in wells or value.get('port') not in wells[value['well']]:
                raise ValueError('Не найдено подключение трубы.')
            key = (value['well'], value['port'])
            if key in used_ports: raise ValueError('Одно подключение занято несколькими участками.')
            used_ports.add(key)
        if edge['from']['well'] == edge['to']['well']: raise ValueError('Участок должен соединять разные колодцы.')
        number(edge.get('diameter')); number(edge.get('pipeWall'))
        if not isinstance(edge.get('waypoints'), list) or len(edge['waypoints']) > 100:
            raise ValueError('Некорректные вершины.')
        for point in edge['waypoints']:
            identifier(point.get('id')); number(point.get('x')); number(point.get('y'))
            if 'autoPort' in point and point['autoPort'] not in [edge['from']['well'], edge['to']['well']]: raise ValueError('Некорректный подвод к стене.')
            for key in ['ground', 'invert']:
                if point.get(key) is not None: number(point[key])
        if not isinstance(edge.get('sections'), list) or not 1 <= len(edge['sections']) <= 100:
            raise ValueError('Некорректные зоны.')
        for section in edge['sections']:
            if 'aroundMaterial' in section and (not isinstance(section['aroundMaterial'], str) or not section['aroundMaterial'].strip() or len(section['aroundMaterial']) > 180):
                raise ValueError('Укажите материал обсыпки.')
            identifier(section.get('id'))
            for key in ['a', 'b', 'width', 'left', 'right', 'topWidth', 'bedding', 'protection', 'casing', 'casingWall']:
                number(section.get(key))
            if not isinstance(section.get('around'), bool): raise ValueError('Некорректная обсыпка.')
            if section.get('method') not in ['trench', 'supports'] or section.get('slopeMode') not in ['angles', 'top']:
                raise ValueError('Некорректная зона.')
            if 'beddingMaterial' in section and (not isinstance(section['beddingMaterial'], str) or len(section['beddingMaterial']) > 100):
                raise ValueError('Некорректный материал подушки.')
        layers(edge.get('layers'), soils, ['start', 'end'], number)
    return model


def layers(values, soils, keys, number):
    if not isinstance(values, list) or len(values) > 40:
        raise ValueError('Некорректные слои грунта.')
    for layer in values:
        if not isinstance(layer.get('soil'), str) or layer['soil'] not in soils: raise ValueError('Грунт отсутствует в справочнике.')
        for key in keys: number(layer.get(key))


def create_app(database_path=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
    db_path = database_path or os.environ.get('DATABASE_PATH', '/data/trench.sqlite3')
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def db():
        connection = sqlite3.connect(db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        if has_request_context() and request.method not in ['GET', 'HEAD', 'OPTIONS']: connection.execute('BEGIN IMMEDIATE')
        try:
            with connection: yield connection
        finally:
            connection.close()

    with db() as connection:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.executescript('''
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schemes(id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), name TEXT NOT NULL,
            model_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS schemes_project ON schemes(project_id);
        CREATE TABLE IF NOT EXISTS scheme_versions(scheme_id TEXT NOT NULL REFERENCES schemes(id), revision INTEGER NOT NULL,
            model_json TEXT NOT NULL, saved_at TEXT NOT NULL, PRIMARY KEY(scheme_id,revision));
        CREATE TABLE IF NOT EXISTS imports(source_key TEXT PRIMARY KEY, scheme_id TEXT NOT NULL REFERENCES schemes(id));

        ''')

    # Additive, transactional migration: model JSON, IDs and previous versions are preserved.
    with db() as connection:
        connection.execute('BEGIN IMMEDIATE')
        for table in ['projects', 'schemes']:
            columns = {row['name'] for row in connection.execute('PRAGMA table_info('+table+')')}
            for column in ['archived_at', 'deleted_at']:
                if column not in columns: connection.execute('ALTER TABLE '+table+' ADD COLUMN '+column+' TEXT')
            if table == 'projects' and 'revision' not in columns:
                connection.execute('ALTER TABLE projects ADD COLUMN revision INTEGER NOT NULL DEFAULT 1')
        connection.execute('PRAGMA user_version=2')

    def active(value):
        if not value: abort(404, description='Объект не найден.')
        if value['deleted_at']: abort(409, description='Объект в корзине. Сначала восстановите его.')
        if value['archived_at']: abort(409, description='Объект в архиве. Сначала верните его в работу.')
        return value

    def view_filter(alias=''):
        view = request.args.get('view', 'active')
        if view not in ['active', 'archived', 'trash']: raise ValueError('Неизвестный раздел.')
        prefix = alias+'.' if alias else ''
        if view == 'trash': return prefix+'deleted_at IS NOT NULL'
        return prefix+'deleted_at IS NULL AND '+prefix+'archived_at IS '+('NOT NULL' if view == 'archived' else 'NULL')

    def project(connection, project_id):
        row = connection.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
        if row is None: return None
        return dict(row)

    def scheme(connection, scheme_id, include_model=True):
        row = connection.execute('SELECT * FROM schemes WHERE id=?', (scheme_id,)).fetchone()
        if row is None: return None
        value = dict(row); model = json.loads(value.pop('model_json'))
        value.update(well_count=sum(w.get('kind') != 'endpoint' for w in model['wells']), endpoint_count=sum(w.get('kind') == 'endpoint' for w in model['wells']), edge_count=len(model['edges']))
        if include_model: value['model'] = model
        return value

    def insert_scheme(connection, project_id, title, model):
        active(project(connection, project_id))
        model = validate_model(model); model['name'] = title; stamp = now(); sid = str(uuid.uuid4())
        connection.execute('INSERT INTO schemes(id,project_id,name,model_json,revision,created_at,updated_at) VALUES(?,?,?,?,?,?,?)', (sid, project_id, title, json.dumps(model, ensure_ascii=False, allow_nan=False), 1, stamp, stamp))
        connection.execute('UPDATE projects SET updated_at=?,revision=revision+1 WHERE id=?', (stamp, project_id))
        return scheme(connection, sid)

    def payload():
        body = request.get_json()
        if not isinstance(body, dict): raise ValueError('Ожидается JSON-объект.')
        return body

    @app.before_request
    def same_origin():
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            origin = request.headers.get('Origin')
            if origin and urlparse(origin).netloc != request.host:
                return jsonify(error='Запрос с другого сайта запрещён.'), 403
            if not request.is_json:
                return jsonify(error='Ожидается JSON.'), 415

    @app.errorhandler(ValueError)
    def invalid(error): return jsonify(error=str(error)), 400

    @app.errorhandler(HTTPException)
    def http_error(error): return jsonify(error=error.description), error.code

    @app.get('/api/health')
    def health():
        with db() as connection: connection.execute('SELECT 1').fetchone()
        return jsonify(ok=True, storage='sqlite', schema=2)

    @app.get('/api/projects')
    def projects():
        with db() as connection:
            rows = connection.execute('SELECT p.*,COUNT(CASE WHEN s.deleted_at IS NULL THEN s.id END) AS scheme_count FROM projects p LEFT JOIN schemes s ON s.project_id=p.id WHERE '+view_filter('p')+' GROUP BY p.id ORDER BY p.updated_at DESC').fetchall()
            return jsonify(projects=[dict(row) for row in rows])

    @app.post('/api/projects')
    def new_project():
        title = name(payload().get('name')); pid = str(uuid.uuid4()); stamp = now()
        with db() as connection:
            connection.execute('INSERT INTO projects(id,name,created_at,updated_at) VALUES(?,?,?,?)', (pid, title, stamp, stamp))
            value = project(connection, pid)
            audit_event('project_create', request.headers.get('X-Auth-User', ''), details={'project': title})
            return jsonify(value), 201

    @app.get('/api/projects/<pid>')
    def get_project(pid):
        with db() as connection:
            value = project(connection, pid)
            if value is None: return jsonify(error='Проект не найден.'), 404
            value['schemes'] = [scheme(connection, row['id'], False) for row in connection.execute('SELECT id FROM schemes WHERE project_id=? AND '+view_filter()+' ORDER BY updated_at DESC', (pid,)).fetchall()]
            return jsonify(value)

    @app.patch('/api/projects/<pid>')
    def rename_project(pid):
        title = name(payload().get('name'))
        with db() as connection:
            if project(connection, pid) is None: return jsonify(error='Проект не найден.'), 404
            active(project(connection, pid))
            connection.execute('UPDATE projects SET name=?,updated_at=?,revision=revision+1 WHERE id=?', (title, now(), pid))
            return jsonify(project(connection, pid))

    @app.post('/api/projects/<pid>/schemes')
    def new_scheme(pid):
        body = payload(); model = body.get('model'); title = name(body.get('name'), model.get('name') if isinstance(model, dict) else None)
        with db() as connection:
            if project(connection, pid) is None: return jsonify(error='Проект не найден.'), 404
            value = insert_scheme(connection, pid, title, model)
            audit_event('scheme_create', request.headers.get('X-Auth-User', ''),
                        details={'scheme': title, 'wells': value.get('well_count'), 'edges': value.get('edge_count')})
            return jsonify(value), 201

    @app.get('/api/schemes/<sid>')
    def get_scheme(sid):
        with db() as connection:
            value = scheme(connection, sid)
            if value:
                active(value); active(project(connection, value['project_id']))
            return (jsonify(value), 200) if value else (jsonify(error='Схема не найдена.'), 404)

    @app.put('/api/schemes/<sid>')
    def save_scheme(sid):
        body = payload(); model = validate_model(body.get('model')); title = name(model['name']); expected = body.get('revision')
        if type(expected) is not int or expected < 1: raise ValueError('Не задана версия схемы.')
        with db() as connection:
            row = connection.execute('SELECT * FROM schemes WHERE id=?', (sid,)).fetchone()
            if row is None: return jsonify(error='Схема не найдена.'), 404
            active(dict(row)); active(project(connection, row['project_id']))
            stamp = now(); serialized = json.dumps(model, ensure_ascii=False, allow_nan=False)
            updated = connection.execute('UPDATE schemes SET name=?,model_json=?,revision=revision+1,updated_at=? WHERE id=? AND revision=?', (title, serialized, stamp, sid, expected))
            if not updated.rowcount:
                audit_event('scheme_save', request.headers.get('X-Auth-User', ''), status='conflict',
                            details={'scheme': title, 'expected_revision': expected, 'actual_revision': row['revision']})
                return jsonify(error='Схема изменена другим инженером.', revision=row['revision']), 409
            connection.execute('INSERT INTO scheme_versions VALUES(?,?,?,?)', (sid, row['revision'], row['model_json'], stamp))
            connection.execute('DELETE FROM scheme_versions WHERE scheme_id=? AND revision < ?', (sid, max(0, expected-19)))
            connection.execute('UPDATE projects SET updated_at=?,revision=revision+1 WHERE id=?', (stamp, row['project_id']))
            audit_event('scheme_save', request.headers.get('X-Auth-User', ''),
                        details={'scheme': title, 'revision': expected + 1})
            return jsonify(scheme(connection, sid, False))

    @app.post('/api/schemes/<sid>/copy')
    def copy_scheme(sid):
        with db() as connection:
            original = scheme(connection, sid)
            if not original: return jsonify(error='Схема не найдена.'), 404
            active(original)
            title = name(payload().get('name'), original['name']+' — копия')
            model = original['model']; model['id'] = str(uuid.uuid4()); model['name'] = title
            value = insert_scheme(connection, original['project_id'], title, model)
            audit_event('scheme_create', request.headers.get('X-Auth-User', ''), details={'scheme': title, 'copied': True})
            return jsonify(value), 201

    @app.post('/api/projects/<pid>/copy')
    def copy_project(pid):
        with db() as connection:
            original = project(connection, pid)
            if not original: return jsonify(error='Проект не найден.'), 404
            active(original)
            title = name(payload().get('name'), original['name']+' — копия'); new_id = str(uuid.uuid4()); stamp = now()
            connection.execute('INSERT INTO projects(id,name,created_at,updated_at) VALUES(?,?,?,?)', (new_id, title, stamp, stamp))
            for row in connection.execute('SELECT id,archived_at FROM schemes WHERE project_id=? AND deleted_at IS NULL', (pid,)).fetchall():
                item = scheme(connection, row['id']); item['model']['id'] = str(uuid.uuid4())
                copied = insert_scheme(connection, new_id, item['name'], item['model'])
                if row['archived_at']: connection.execute('UPDATE schemes SET archived_at=? WHERE id=?', (now(), copied['id']))
            audit_event('project_create', request.headers.get('X-Auth-User', ''), details={'project': title, 'copied': True})
            return jsonify(project(connection, new_id)), 201

    @app.post('/api/import')
    def import_model():
        body = payload(); model = validate_model(body.get('model')); title = name(body.get('project_name'), model['name']); token = body.get('source_key')
        if token == 'legacy-model':
            raw = body.get('source_json')
            if not isinstance(raw, str) or json.loads(raw) != model: raise ValueError('Некорректный источник переноса.')
            token = 'legacy-' + hashlib.sha256(raw.encode('utf-8')).hexdigest()
        if not isinstance(token, str) or not 1 <= len(token) <= 300: raise ValueError('Некорректный ключ импорта.')
        # Atomic idempotency for an import retried after a lost connection.
        with db() as connection:
            row = connection.execute('SELECT scheme_id FROM imports WHERE source_key=?', (token,)).fetchone()
            if row: return jsonify(scheme(connection, row['scheme_id']))
            pid = str(uuid.uuid4()); stamp = now()
            connection.execute('INSERT INTO projects(id,name,created_at,updated_at) VALUES(?,?,?,?)', (pid, title, stamp, stamp))
            item = insert_scheme(connection, pid, model['name'], model)
            connection.execute('INSERT INTO imports VALUES(?,?)', (token, item['id']))
            audit_event('scheme_create', request.headers.get('X-Auth-User', ''), details={'scheme': model['name'], 'imported': True})
            return jsonify(item), 201

    def require_revision(body, value):
        expected = body.get('revision')
        if type(expected) is not int or expected < 1: raise ValueError('Не задана версия объекта.')
        if expected != value['revision']: abort(409, description='Объект изменился. Обновите список и повторите действие.')

    def change_state(kind, object_id):
        body = payload(); action = body.get('action')
        if action not in ['archive', 'unarchive', 'trash', 'restore']: raise ValueError('Неизвестное действие.')
        table = 'projects' if kind == 'project' else 'schemes'
        with db() as connection:
            value = project(connection, object_id) if kind == 'project' else scheme(connection, object_id, False)
            if not value: abort(404, description='Объект не найден.')
            require_revision(body, value)
            if kind == 'scheme': active(project(connection, value['project_id']))
            if action == 'restore':
                if not value['deleted_at']: abort(409, description='Объект не находится в корзине.')
                column, target = 'deleted_at', None
            else:
                if value['deleted_at']: abort(409, description='Сначала восстановите объект из корзины.')
                if action == 'archive':
                    if value['archived_at']: abort(409, description='Объект уже находится в архиве.')
                    column, target = 'archived_at', now()
                elif action == 'unarchive':
                    if not value['archived_at']: abort(409, description='Объект не находится в архиве.')
                    column, target = 'archived_at', None
                else: column, target = 'deleted_at', now()
            connection.execute('UPDATE '+table+' SET '+column+'=?,updated_at=?,revision=revision+1 WHERE id=?', (target, now(), object_id))
            if kind == 'project':
                # Invalidate editors opened before the project was archived/trashed and restored.
                connection.execute('UPDATE schemes SET revision=revision+1 WHERE project_id=?', (object_id,))
                audit_event('state_change', request.headers.get('X-Auth-User', ''), details={'kind': kind, 'action': action})
                return jsonify(project(connection, object_id))
            connection.execute('UPDATE projects SET updated_at=?,revision=revision+1 WHERE id=?', (now(), value['project_id']))
            audit_event('state_change', request.headers.get('X-Auth-User', ''), details={'kind': kind, 'action': action})
            return jsonify(scheme(connection, object_id, False))

    @app.post('/api/projects/<pid>/state')
    def project_state(pid): return change_state('project', pid)

    @app.post('/api/schemes/<sid>/state')
    def scheme_state(sid): return change_state('scheme', sid)

    def purge(kind, object_id):
        body = payload()
        with db() as connection:
            value = project(connection, object_id) if kind == 'project' else scheme(connection, object_id, False)
            if not value: abort(404, description='Объект не найден.')
            require_revision(body, value)
            if not value['deleted_at']: abort(409, description='Окончательно удалить можно только объект из корзины.')
            if body.get('confirm_name') != value['name']: raise ValueError('Для удаления введите точное название объекта.')
            ids = [row['id'] for row in connection.execute('SELECT id FROM schemes WHERE project_id=?', (object_id,))] if kind == 'project' else [object_id]
            for sid in ids:
                connection.execute('DELETE FROM imports WHERE scheme_id=?', (sid,))
                connection.execute('DELETE FROM scheme_versions WHERE scheme_id=?', (sid,))
                connection.execute('DELETE FROM schemes WHERE id=?', (sid,))
            if kind == 'project': connection.execute('DELETE FROM projects WHERE id=?', (object_id,))
            else: connection.execute('UPDATE projects SET updated_at=?,revision=revision+1 WHERE id=?', (now(), value['project_id']))
            return jsonify(ok=True)

    @app.delete('/api/projects/<pid>')
    def purge_project(pid): return purge('project', pid)

    @app.delete('/api/schemes/<sid>')
    def purge_scheme(sid): return purge('scheme', sid)

    return app


app = create_app() if not os.environ.get('TRENCH_TESTING') else None
