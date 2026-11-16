"""Intranet web service. Start with python webapp/app.py --host 0.0.0.0."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import math
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
import time
from urllib.request import Request, urlopen
from flask import Flask, jsonify, request, send_file, session
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent




AUDIT_URL = os.environ.get("AUDIT_URL", "http://audit:8080")


def audit_event(action, user, logger, **fields):
    """Fire-and-forget audit event; never breaks the request on failure."""
    if not user:
        return
    try:
        payload = json.dumps({"tool": "bookmarks", "action": action, "user": user, **fields}).encode()
        urlopen(Request(AUDIT_URL + "/audit/event", data=payload,
                        headers={"Content-Type": "application/json"}, method="POST"),
                timeout=2).close()
    except Exception:
        logger.exception("Bookmarks audit event %s lost", action)


def create_app(config=None):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(
        SECRET_KEY=os.environ.get("PDF_WEB_SECRET") or secrets.token_hex(32),
        MAX_CONTENT_LENGTH=200 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("PDF_WEB_HTTPS") == "1",
        DATA_DIR=os.environ.get("PDF_WEB_DATA_DIR", str(ROOT / "data")),
        JOB_TTL=3600, PROCESS_TIMEOUT=300, MAX_PAGES=2500,
        WORKERS=2, MAX_JOBS=8,
    )
    if config:
        app.config.update(config)
    job_root = Path(app.config["DATA_DIR"]).resolve() / "jobs"
    job_root.mkdir(parents=True, exist_ok=True)
    jobs = {}
    lock = threading.RLock()
    pool = ThreadPoolExecutor(max_workers=app.config["WORKERS"], thread_name_prefix="pdf-job")
    stop = threading.Event()
    app.extensions["pdf_jobs"] = {"jobs": jobs, "pool": pool, "stop": stop, "root": job_root}
    def purge():
        with lock:
            expired = [key for key, job in jobs.items()
                       if job["status"] in {"done", "error"} and time.time() - job["finished"] > app.config["JOB_TTL"]]
            for key in expired:
                shutil.rmtree(job_root / key)
                del jobs[key]
            # Remove orphaned files after a service restart, without touching recent jobs.
            for folder in job_root.iterdir():
                if (folder.name not in jobs and folder.is_dir() and len(folder.name) == 48
                        and all(c in "0123456789abcdef" for c in folder.name)
                        and time.time() - folder.stat().st_mtime > app.config["JOB_TTL"] + app.config["PROCESS_TIMEOUT"]):
                    shutil.rmtree(folder)

    def janitor():
        while not stop.wait(60):
            try:
                purge()
            except OSError:
                app.logger.exception("Failed to clean temporary PDF jobs")
    threading.Thread(target=janitor, daemon=True, name="pdf-cleanup").start()

    def run_job(key):
        folder = job_root / key
        with lock:
            jobs[key]["status"] = "processing"
        status = "error"
        details = {"error": "Не удалось обработать PDF. Обратитесь к администратору."}
        try:
            completed = subprocess.run([sys.executable, str(ROOT / "worker.py"), str(folder)],
                                       timeout=app.config["PROCESS_TIMEOUT"], capture_output=True,
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if completed.returncode:
                app.logger.error("PDF worker failed for job %s (exit %s)", key, completed.returncode)
                raise RuntimeError("Не удалось обработать PDF. Обратитесь к администратору.")
            details = json.loads((folder / "details.json").read_text(encoding="utf-8"))
            status = "done" if details["ok"] else "error"
        except subprocess.TimeoutExpired:
            details = {"error": "Обработка заняла больше 5 минут. Разделите PDF на части и повторите."}
        except Exception:
            app.logger.exception("PDF processing failed for job %s", key)
            details = {"error": "Не удалось обработать PDF. Обратитесь к администратору."}
        finally:
            # Keep only result files needed for downloading until expiry.
            for filename in ("input.pdf", "options.json", "details.json"):
                try:
                    (folder / filename).unlink(missing_ok=True)
                except OSError:
                    app.logger.exception("Failed to remove temporary PDF job input")
            with lock:
                jobs[key].update(status=status, result=details, finished=time.time())
                info = dict(jobs[key])
            audit_event("process", info.get("audit_user"), app.logger,
                        user_name=info.get("audit_name"),
                        status=status, pages=details.get("pages"), duration_ms=int(
                            (time.time() - info.get("started", time.time())) * 1000),
                        error=details.get("error"),
                        details={"added": details.get("added"),
                                 "allow_incomplete": details.get("allow_incomplete"),
                                 "warnings": details.get("warnings")})

    @app.before_request
    def session_and_origin():
        if "owner" not in session:
            session["owner"] = secrets.token_hex(24)
        if request.method == "POST":
            # Custom header prevents cross-origin forms; no CORS is enabled.
            if request.headers.get("X-PDF-Service") != "1":
                return jsonify(error="Обновите страницу и повторите загрузку."), 403
            if request.headers.get("Sec-Fetch-Site") == "cross-site":
                return jsonify(error="Загрузка разрешена только со страницы сервиса."), 403

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        embedded = app.config.get("PORTAL_EMBEDDED", False)
        response.headers["X-Frame-Options"] = "SAMEORIGIN" if embedded else "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        ancestors = "'self'" if embedded else "'none'"
        response.headers["Content-Security-Policy"] = f"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors {ancestors}; base-uri 'self'; form-action 'self'"
        return response

    @app.errorhandler(413)
    def too_big(_):
        return jsonify(error="Файл слишком большой. Максимальный размер — 200 МБ."), 413

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {404: "Файл не найден или срок хранения истёк. Загрузите PDF заново.", 405: "Метод запроса не поддерживается."}
        return jsonify(error=messages.get(error.code, "Некорректный запрос.")), error.code

    @app.get("/")
    def index():
        return send_file(ROOT / "static" / "index.html")

    @app.get("/api/health")
    def health():
        return jsonify(service="pdf-bookmarks", status="ok")

    @app.post("/api/jobs")
    def upload():
        purge()
        file = request.files.get("file")
        if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
            return jsonify(error="Выберите файл в формате PDF."), 400
        try:
            start = int(request.form.get("start") or "1")
            end = int(request.form["end"]) if request.form.get("end") else None
            scale = float(request.form.get("scale") or "1")
            if start < 1 or (end is not None and end < start) or not math.isfinite(scale) or not 0.25 <= scale <= 4:
                raise ValueError()
        except (ValueError, OverflowError):
            return jsonify(error="Проверьте диапазон страниц и масштаб штампа (от 0,25 до 4)."), 400
        if not file.stream.read(1024).lstrip().startswith(b"%PDF-"):
            return jsonify(error="Содержимое файла не похоже на PDF. Проверьте документ."), 400
        file.stream.seek(0)
        with lock:
            if sum(job["status"] in {"uploading", "queued", "processing"} for job in jobs.values()) >= app.config["MAX_JOBS"]:
                return jsonify(error="Сервис занят. Подождите завершения текущих заданий и повторите."), 429
            key = secrets.token_hex(24)
            filename = file.filename.replace("\\", "/").split("/")[-1]
            filename = "".join(char for char in filename if ord(char) >= 32)[:180] or "document.pdf"
            jobs[key] = {"owner": session["owner"], "filename": filename, "status": "uploading",
                         "audit_user": request.headers.get("X-Auth-User", ""),
                         "audit_name": request.headers.get("X-Auth-Name", ""),
                         "started": time.time()}
        folder = job_root / key
        try:
            folder.mkdir()
            file.save(folder / "input.pdf")
            options = {"start": start, "end": end, "scale": scale,
                       "allow_incomplete": request.form.get("allow_incomplete") == "true", "max_pages": app.config["MAX_PAGES"]}
            (folder / "options.json").write_text(json.dumps(options), encoding="utf-8")
            with lock:
                jobs[key]["status"] = "queued"
            pool.submit(run_job, key)
        except Exception:
            with lock:
                jobs.pop(key, None)
            shutil.rmtree(folder, ignore_errors=True)
            app.logger.exception("Could not save uploaded PDF")
            return jsonify(error="Не удалось принять файл. Проверьте свободное место на сервере."), 500
        return jsonify(id=key), 202

    def owned_job(key):
        purge()
        with lock:
            job = jobs.get(key)
            return dict(job) if job and job["owner"] == session["owner"] else None

    @app.get("/api/jobs/<key>")
    def status(key):
        job = owned_job(key)
        if not job:
            return jsonify(error="Задание не найдено или срок хранения истёк. Загрузите PDF заново."), 404
        result = {"id": key, "status": job["status"], "filename": job["filename"]}
        if job["status"] in {"done", "error"}:
            result.update(job["result"])
        return jsonify(result)

    @app.get("/api/jobs/<key>/download/<kind>")
    def download(key, kind):
        job = owned_job(key)
        if not job or job["status"] != "done" or kind not in {"pdf", "csv"}:
            return jsonify(error="Файл недоступен. Загрузите PDF заново."), 404
        audit_event("download", job.get("audit_user") or request.headers.get("X-Auth-User", ""),
                    app.logger, user_name=job.get("audit_name") or request.headers.get("X-Auth-Name", ""),
                    details={"kind": kind})
        path = job_root / key / ("result.pdf" if kind == "pdf" else "bookmarks.csv")
        stem = Path(job["filename"]).stem
        name = f"{stem}_с_закладками.pdf" if kind == "pdf" else f"{stem}_закладки.csv"
        # Open under the lock so expiry cannot remove the file before send_file opens it.
        with lock:
            return send_file(path, as_attachment=True, download_name=name,
                             mimetype="application/pdf" if kind == "pdf" else "text/csv; charset=utf-8")

    return app


if __name__ == "__main__":
    from waitress import serve
    parser = argparse.ArgumentParser(description="Внутренний сервис закладок PDF")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    print(f"PDF service: http://{args.host}:{args.port}", flush=True)
    serve(app, host=args.host, port=args.port, threads=8,
          max_request_body_size=app.config["MAX_CONTENT_LENGTH"], channel_timeout=360)
