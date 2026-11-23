"""GESN norm matching: VOR xlsx in, ranked norm candidates + xlsx out.

Conventions copied from apps/kac/app.py (job engine, audit, guards)
and apps/bookmarks/webapp/app.py (Flask factory, error handlers).
"""
import json
import os
import re
import secrets
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from email.header import decode_header, make_header
from pathlib import Path
from threading import Event, Lock, Thread
from urllib.request import Request, urlopen

from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from embed import embed_query, rerank
from retrieval import search_candidates

ROOT = Path(__file__).resolve().parent
TTL = 7 * 24 * 3600  # result xlsx retention, seconds
MAX_VOR_ROWS = 1000
MAX_SHEETS = 20
MAX_ROWS_PER_SHEET = 10000
MAX_CELLS = 100000

NORMS_DSN = os.environ.get("NORMS_DSN", "")
SERVICE_TOKEN = os.environ.get("GESN_TOKEN", "")
ROUTER_BASE_URL = os.environ.get("ROUTER_BASE_URL", "https://routerai.ru/api/v1")
ROUTER_API_KEY = os.environ.get("ROUTER_API_KEY", "")
SUB_MODEL = os.environ.get("GESN_MODEL", "deepseek/deepseek-v4.1-flash")
AUDIT_URL = os.environ.get("AUDIT_URL", "http://audit:8080")


def auth_display_name(value):
    """Decode the RFC 2047 X-Auth-Name header set by portal auth."""
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return value or ""


def audit_event(action, user, logger=None, **fields):
    """Fire-and-forget audit event; never breaks the request on failure."""
    if not user:
        return
    try:
        payload = json.dumps(
            {"tool": "gesn-match", "action": action, "user": user, **fields}
        ).encode()
        urlopen(Request(AUDIT_URL + "/audit/event", data=payload,
                        headers={"Content-Type": "application/json"}, method="POST"),
                timeout=2).close()
    except Exception:
        if logger is not None:
            logger.exception("gesn-match audit event %s lost", action)


def db():
    import psycopg
    return psycopg.connect(NORMS_DSN, row_factory=None)


def apply_schema():
    sql = (ROOT / "schema.sql").read_text(encoding="utf-8")
    with db() as con:
        con.execute(sql)  # type: ignore[call-overload]
        con.commit()


HEADER_PATTERNS = {
    "name": re.compile(r"наимен|работ|позиц|содержан", re.I),
    "unit": re.compile(r"ед[\.\s]*изм|измер|unit", re.I),
    "qty": re.compile(r"кол|объем|объём|к-во|колич", re.I),
}


def parse_vor(data: bytes) -> list[dict]:
    """Extract VOR positions from xlsx bytes. Caps mirror kdfp_smb_reader.py."""
    from openpyxl import load_workbook
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        book = load_workbook(tmp_path, read_only=True, data_only=True)
        if len(book.sheetnames) > MAX_SHEETS:
            raise ValueError(f"В книге больше {MAX_SHEETS} листов.")
        rows_out = []
        cells = 0
        for sheet in book.worksheets:
            grid = []
            for row in sheet.iter_rows(values_only=True):
                if len(grid) >= MAX_ROWS_PER_SHEET:
                    break
                grid.append([(c if c is not None else "") for c in row])
                cells += len(row)
                if cells > MAX_CELLS:
                    raise ValueError("Слишком большая книга (лимит 100 тыс. ячеек).")
            header_idx, mapping = find_header(grid)
            start = header_idx + 1 if header_idx is not None else 0
            if mapping is None:
                mapping = {"name": 0, "unit": 1, "qty": 2}
            for i in range(start, len(grid)):
                row = grid[i]
                name = str(row[mapping["name"]]).strip() if mapping["name"] < len(row) else ""
                if not name:
                    continue
                unit = str(row[mapping["unit"]]).strip() if mapping["unit"] < len(row) else ""
                qty = str(row[mapping["qty"]]).strip() if mapping["qty"] < len(row) else ""
                rows_out.append({
                    "row_no": len(rows_out) + 1,
                    "name": name, "unit": unit, "quantity": qty,
                    "sheet": sheet.title,
                })
                if len(rows_out) >= MAX_VOR_ROWS:
                    raise ValueError(f"Больше {MAX_VOR_ROWS} позиций — разбейте ведомость.")
        return rows_out
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def find_header(grid):
    for idx, row in enumerate(grid[:10]):
        cells = [str(c).strip() for c in row]
        mapping = {}
        for key, pattern in HEADER_PATTERNS.items():
            for col, cell in enumerate(cells):
                if cell and pattern.search(cell):
                    mapping[key] = col
                    break
        if "name" in mapping:
            mapping.setdefault("unit", 1)
            mapping.setdefault("qty", 2)
            return idx, mapping
    return None, None


def load_profile(name: str) -> dict:
    import yaml
    path = ROOT / "profiles" / f"{name}.yaml"
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


STATUS_ALIASES = {
    "ok": "ok", "подходит": "ok", "applicable": "ok",
    "clarify": "clarify", "уточнить": "clarify",
    "requires_clarification": "clarify", "need_clarification": "clarify",
    "reject": "reject", "отклонён": "reject", "not_applicable": "reject",
}


def parse_verdicts(content: str, count: int) -> dict[int, dict]:
    """Accept our {verdicts:[...]} schema and the model's own shapes.

    Fallbacks, in order: verdicts list; per-candidate dict with index/
    candidate_index; decision/applicable synonyms. Never raises."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        start, end = content.find("{"), content.rfind("}")
        try:
            data = json.loads(content[start:end + 1]) if start != -1 and end > start else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    if not isinstance(data, dict):
        return {}
    items = data.get("verdicts")
    if isinstance(items, list):
        return {v.get("index"): v for v in items if isinstance(v, dict)}
    for key in ("candidate_index", "index"):
        if isinstance(data.get(key), int):
            return {data[key]: data}
    if "decision" in data or "applicable" in data:
        return {0: data}
    return {}


def normalize_verdict(verdict: dict) -> tuple[str, str, list]:
    raw = str(verdict.get("status", "") or verdict.get("decision", "")).strip().lower()
    if not raw and isinstance(verdict.get("applicable"), bool):
        raw = "ok" if verdict["applicable"] else "reject"
    status = STATUS_ALIASES.get(raw, "clarify")
    rationale = str(verdict.get("rationale", "") or verdict.get("reason", ""))[:2000]
    missing = verdict.get("missing", [])
    if isinstance(missing, str):
        missing = [missing]
    return status, rationale, list(missing or [])


def llm_verify(position: dict, candidates: list[dict], profile: dict) -> list[dict]:
    """LLM applicability check. Never invents codes: only reorders/labels input."""
    if not ROUTER_API_KEY or not candidates:
        for cand in candidates:
            cand["status"] = "unverified"
            cand["rationale"] = "Нет ключа LLM — только кандидаты поиска."
        return candidates
    checklist = "\n".join(f"- {item}" for item in profile.get("checklist", []))
    stops = "\n".join(f"- {item}" for item in profile.get("stop_conditions", []))
    cand_text = "\n\n".join(
        f"[{i}] {c.get('code')} — {c.get('title')} (ед.: {c.get('unit')})\n"
        f"Состав работ: {'; '.join(c.get('work_composition') or [])}"
        for i, c in enumerate(candidates)
    )
    prompt = (
        f"Позиция ВОР: {position['name']} (ед.: {position.get('unit')}, кол-во: {position.get('quantity')}).\n"
        f"Кандидаты из каталога ГЭСН:\n{cand_text}\n\n"
        f"Проверь применимость каждого кандидата по критериям:\n{checklist}\n"
        f"Стоп-условия (такой кандидат — clarify):\n{stops}\n\n"
        "Ответь СТРОГО JSON, например: "
        "{\"verdicts\": [{\"index\": 0, \"status\": \"clarify\", "
        "\"rationale\": \"...\", \"missing\": [\"...\"]}]}. "
        "Допустимые status: ok, clarify, reject. "
        "Шифры не сочиняй, оценивай только данный список."
    )
    body = json.dumps({
        "model": SUB_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }).encode()
    try:
        req = Request(
            ROUTER_BASE_URL.rstrip("/") + "/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {ROUTER_API_KEY}"},
            method="POST",
        )
        with urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"] or ""
        verdicts = parse_verdicts(content, len(candidates))
        if not verdicts:
            raise ValueError(f"unparsed LLM verdict: {content[:200]}")
    except Exception as error:
        import logging
        logging.getLogger("gesn-match").exception("LLM verify failed: %s", error)
        for cand in candidates:
            cand["status"] = "error_retry"
            cand["rationale"] = "Проверка не выполнена (LLM недоступен)."
        return candidates
    for i, cand in enumerate(candidates):
        status, rationale, missing = normalize_verdict(verdicts.get(i, {}))
        cand["status"] = status
        cand["rationale"] = rationale
        cand["missing"] = missing
    return candidates


def write_report(rows: list[dict], path: Path):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Подбор ГЭСН"
    sheet.append(["№", "Позиция ВОР", "Ед.", "Кол-во", "Шифр", "Наименование нормы",
                  "Ед. нормы", "Статус", "Обоснование", "Источник (таблица)"])
    for row in rows:
        cands = row.get("candidates", [])
        if not cands:
            sheet.append([row["row_no"], row["name"], row.get("unit"), row.get("quantity"),
                          "", "", "", "not_found",
                          "Кандидатов не найдено — передать сметчику.", ""])
            continue
        for cand in cands:
            sheet.append([row["row_no"], row["name"], row.get("unit"), row.get("quantity"),
                          cand.get("code"), cand.get("title"), cand.get("unit"),
                          cand.get("status"), cand.get("rationale"),
                          cand.get("table_code") or cand.get("source_ref")])
    book.save(path)


def create_match_app():
    app = Flask(__name__, static_folder=None)
    app.config.update(SECRET_KEY=secrets.token_hex(32),
                      MAX_CONTENT_LENGTH=200 * 1024 * 1024, MAX_FORM_PARTS=501)
    root = Path(os.getenv("GESN_DATA_DIR", str(ROOT / "data"))).resolve() / "gesn-jobs"
    jobs = {}
    lock = Lock()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gesn")
    stop = Event()

    def janitor():
        while not stop.wait(3600):
            with lock:
                for folder in root.iterdir():
                    job = jobs.get(folder.name)
                    if (folder.is_dir() and re.fullmatch(r"[a-f0-9]{32}", folder.name)
                            and time.time() - (job.get("finished", time.time()) if job
                                               else folder.stat().st_mtime) > TTL):
                        shutil.rmtree(folder, ignore_errors=True)
                        if not folder.exists():
                            jobs.pop(folder.name, None)

    root.mkdir(parents=True, exist_ok=True)
    Thread(target=janitor, daemon=True, name="gesn-cleanup").start()
    app.extensions["gesn_jobs"] = {"stop": stop, "pool": pool}

    def check_token():
        if SERVICE_TOKEN and request.headers.get("Authorization") != f"Bearer {SERVICE_TOKEN}":
            return jsonify(error="Недопустимый токен сервиса."), 401
        return None

    def run_job(key, vor_data, collection, edition_id, top_k, profile_name):
        folder = root / key
        profile = load_profile(profile_name)
        status = {"status": "error", "error": "Не удалось обработать ведомость."}
        try:
            positions = parse_vor(vor_data)
            with db() as con:
                query_vec = embed_query  # resolved per row below
                rows_out = []
                total = len(positions)
                for pos in positions:
                    with lock:
                        jobs[key].update(stage="matching",
                                         progress=0.05 + 0.9 * (pos["row_no"] - 1) / max(total, 1))
                    vec = query_vec(f"{pos['name']} {pos.get('unit', '')}".strip())
                    cands = search_candidates(con, f"{pos['name']} {pos.get('unit', '')}".strip(),
                                              vec, collection, edition_id, limit=30)
                    cands = rerank(f"{pos['name']} {pos.get('unit', '')}".strip(), cands, top_k=5)
                    for c in cands:
                        with db() as con2:
                            res = con2.execute(
                                "SELECT res_code, res_name, quantity, res_kind FROM norm_resources "
                                "WHERE norm_code = %s AND collection = %s AND edition_id = %s "
                                "ORDER BY res_kind, res_code",
                                (c["code"], collection, edition_id)).fetchall()
                        c["machines"] = "; ".join(
                            f"{r[1] or r[0]} ({r[2]})" for r in res if r[3] == "machine")[:500]
                    verified = llm_verify(pos, cands[:5], profile)[:top_k]
                    needs_clar = any(v.get("status") == "clarify" for v in verified)
                    rows_out.append({**pos, "candidates": verified,
                                     "needs_clarification": needs_clar or not verified})
            write_report(rows_out, folder / "result.xlsx")
            status = {"status": "done", "rows": rows_out}
        except ValueError as error:
            status = {"status": "error", "error": str(error)}
        except Exception:
            app.logger.exception("gesn-match job %s failed", key)
            status = {"status": "error", "error": "Не удалось обработать ведомость."}
        finally:
            with lock:
                jobs[key].update(status, finished=time.time())
                info = dict(jobs[key])
            audit_event("match", info.get("audit_user"), app.logger,
                        user_name=info.get("audit_name"),
                        status=status["status"],
                        duration_ms=int((time.time() - info.get("started", time.time())) * 1000),
                        error=status.get("error"),
                        details={"positions": info.get("positions"),
                                 "collection": collection} if info.get("positions") else None)

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = \
            "default-src 'self'; object-src 'none'; frame-ancestors 'self'; base-uri 'none'"
        return response

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="Файл больше 200 МБ."), 413

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.get("/api/health")
    def health():
        try:
            with db() as con:
                count = con.execute("SELECT count(*) FROM norms").fetchone()[0]
            return {"ok": True, "norms": count}
        except Exception as error:
            return {"ok": False, "error": str(error)[:200]}, 500

    @app.get("/api/v1/editions")
    def editions():
        denied = check_token()
        if denied:
            return denied
        with db() as con:
            rows = con.execute(
                "SELECT id, base_name, price_level, creation_date, decree FROM editions ORDER BY id"
            ).fetchall()
        return {"editions": [
            {"id": r[0], "base_name": r[1], "price_level": r[2],
             "creation_date": r[3], "decree": r[4]} for r in rows]}

    @app.post("/api/v1/match")
    def match():
        denied = check_token()
        if denied:
            return denied
        vor = request.files.get("vor_file")
        collection = (request.form.get("collection") or "ГЭСН").strip()
        edition_id = (request.form.get("edition_id") or "").strip()
        try:
            top_k = min(max(int(request.form.get("top_k", 3)), 1), 5)
        except ValueError:
            return jsonify(error="top_k — число 1..5."), 400
        profile_name = (request.form.get("profile") or "building").strip()
        if not vor or not (vor.filename or "").lower().endswith(".xlsx"):
            return jsonify(error="Приложите ВОР (.xlsx) полем vor_file."), 400
        if collection not in ("ГЭСН", "ГЭСНм", "ГЭСНр", "ГЭСНп"):
            return jsonify(error="Неизвестный сборник."), 400
        if not edition_id:
            return jsonify(error="Укажите edition_id (см. /api/v1/editions)."), 400
        if not re.fullmatch(r"[A-Za-z0-9_.~-]{1,80}", profile_name):
            return jsonify(error="Недопустимый profile."), 400
        key = secrets.token_hex(16)
        folder = root / key
        with lock:
            if sum("finished" not in job for job in jobs.values()) >= 4:
                return jsonify(error="Очередь заполнена. Повторите позже."), 429
            jobs[key] = {"status": "queued", "stage": "queued", "progress": 0.05,
                         "audit_user": request.headers.get("X-Auth-User", ""),
                         "audit_name": auth_display_name(request.headers.get("X-Auth-Name", "")),
                         "started": time.time()}
        try:
            folder.mkdir(parents=True)
            data = vor.read()
            (folder / "vor.xlsx").write_bytes(data)
            pool.submit(run_job, key, data, collection, edition_id, top_k,
                        profile_name)
        except Exception:
            with lock:
                jobs.pop(key, None)
            shutil.rmtree(folder, ignore_errors=True)
            app.logger.exception("Could not stage gesn-match inputs")
            return jsonify(error="Не удалось сохранить загруженный файл."), 500
        return jsonify(id=key), 202

    @app.get("/api/v1/match/<key>")
    def job_status(key):
        denied = check_token()
        if denied:
            return denied
        if not re.fullmatch(r"[a-f0-9]{32}", key):
            return jsonify(error="Нет такого задания."), 404
        with lock:
            job = jobs.get(key)
            if not job:
                return jsonify(error="Нет такого задания."), 404
            info = {k: v for k, v in job.items()
                    if k not in ("audit_user", "audit_name", "started", "finished")}
        return info

    @app.get("/api/v1/match/<key>/xlsx")
    def job_xlsx(key):
        denied = check_token()
        if denied:
            return denied
        if not re.fullmatch(r"[a-f0-9]{32}", key):
            return jsonify(error="Нет такого задания."), 404
        with lock:
            job = jobs.get(key)
        if not job or job.get("status") != "done":
            return jsonify(error="Результат ещё не готов."), 404
        path = root / key / "result.xlsx"
        if not path.is_file():
            return jsonify(error="Файл результата отсутствует."), 404
        audit_event("download", job.get("audit_user") or request.headers.get("X-Auth-User", ""),
                    app.logger,
                    user_name=job.get("audit_name") or auth_display_name(
                        request.headers.get("X-Auth-Name", "")))
        return send_file(path, as_attachment=True, download_name="Подбор ГЭСН.xlsx")

    return app
