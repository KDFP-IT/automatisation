"""Accept a Word template and a tree of offers from the KAC portal tool."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import csv
from http.client import HTTPConnection, HTTPSConnection, HTTPException
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
from threading import Event, Lock, Thread, Timer
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile

from flask import Flask, Response, jsonify, request, send_file, send_from_directory, session

ROOT = Path(__file__).resolve().parent
UI = ROOT / "static" / "ui"
SECTION = re.compile(r"Раздел\s+(\d+)\s*[-–—]\s*\S.*", re.IGNORECASE)
WINDOWS_RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\.|$)", re.I)
DOWNLOADS = {"pdf": ("result.pdf", "КАЦ — готовый комплект.pdf"),
             "zip": ("images.zip", "КАЦ — картинки по разделам.zip")}
TTL = 3600


def upload_path(name):
    parts = name.split("/")
    if len(parts) not in (2, 3, 4) or any(
        not part or part in {".", ".."} or part[-1] in ". " or len(part) > 160
        or re.search(r'[<>:"\\|?*\x00-\x1f]', part) or WINDOWS_RESERVED.match(part)
        for part in parts
    ):
        raise ValueError("Проверьте имена папок и файлов КП.")
    folder, filename = parts[-2:]
    section = SECTION.fullmatch(folder)
    if section is None or not filename.lower().endswith(".pdf"):
        raise ValueError("КП должны лежать в папках вида «Раздел 1 - Контактная сеть».")
    return int(section[1]), folder, filename, "/".join(parts[:-1])

AUDIT_URL = os.environ.get("AUDIT_URL", "http://audit:8080")


def audit_event(action, user, logger=None, **fields):
    """Fire-and-forget audit event; never breaks the request on failure."""
    if not user:
        return
    try:
        payload = json.dumps({"tool": "kac", "action": action, "user": user, **fields}).encode()
        urlopen(Request(AUDIT_URL + "/audit/event", data=payload,
                        headers={"Content-Type": "application/json"}, method="POST"),
                timeout=2).close()
    except Exception:
        if logger is not None:
            logger.exception("KAC audit event %s lost", action)


def create_kac_app():
    app = Flask(__name__, static_folder=None)
    app.config.update(SECRET_KEY=secrets.token_hex(32), SESSION_COOKIE_NAME="portal_kac",
                      SESSION_COOKIE_PATH="/kac/", SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=os.getenv("PDF_WEB_HTTPS") == "1",
                      MAX_CONTENT_LENGTH=200 * 1024 * 1024, MAX_FORM_PARTS=501)
    available = os.name == "nt" or (
        os.getenv("KAC_LOCAL_EXPORT") == "1" and shutil.which("soffice") is not None
    )
    worker_url = os.getenv("KAC_WORKER_URL") if not available else None
    upstream = urlsplit(worker_url) if worker_url else None
    if upstream and (not upstream.hostname or upstream.scheme not in {"http", "https"}
            or upstream.username is not None or upstream.path not in {"", "/"}
            or upstream.query or upstream.fragment):
        raise ValueError("KAC_WORKER_URL must be a Windows worker HTTP(S) origin")
    configured_template = os.getenv("KAC_TEMPLATE_DOCX")
    template = Path(configured_template).resolve() if configured_template else None
    root = Path(os.getenv("PDF_WEB_DATA_DIR", str(ROOT / "data"))).resolve() / "kac-jobs"
    jobs = {}
    lock = Lock()
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kac")
    stop = Event()
    app.extensions["kac_jobs"] = {"stop": stop, "pool": pool}

    def janitor():
        while not stop.wait(60):
            with lock:
                for folder in root.iterdir():
                    job = jobs.get(folder.name)
                    if (folder.is_dir() and re.fullmatch(r"[a-f0-9]{32}", folder.name)
                            and time.time() - (job.get("finished", time.time()) if job
                                               else folder.stat().st_mtime) > TTL):
                        shutil.rmtree(folder, ignore_errors=True)
                        if not folder.exists():
                            jobs.pop(folder.name, None)

    if available:
        root.mkdir(parents=True, exist_ok=True)
        Thread(target=janitor, daemon=True, name="kac-cleanup").start()

    def run_job(key, sections):
        folder = root / key
        covered = len(sections)
        with lock:
            jobs[key].update(status="processing", stage="preparing", progress=0.1,
                             sections_done=0, sections_total=covered)
        try:
            worker = ROOT / "assemble.py"
            result = folder / "result"
            offers = folder / "offers"
            if len(sections) == 1:
                offers /= next(iter(sections.values()))
            process = subprocess.Popen(
                [sys.executable, "-u", str(worker), str(folder / "source.docx"), str(offers),
                 "-o", str(result), "--yes"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            tail = deque(maxlen=40)
            expired = []

            def stop():
                expired.append(True)
                process.kill()

            watchdog = Timer(900, stop)
            watchdog.start()
            try:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        tail.append(line)
                    if re.match(r"^Раздел\s+\d+\s+—", line):
                        with lock:
                            job = jobs[key]
                            done = job.get("sections_done", 0) + 1
                            job.update(sections_done=done, stage="rendering",
                                       progress=round(0.15 + 0.75 * done / max(covered, 1), 3))
                    elif "Обновление оглавления" in line:
                        with lock:
                            jobs[key].update(stage="exporting", progress=0.92)
            finally:
                watchdog.cancel()
                process.stdout.close()
                code = process.wait()
            if expired:
                raise subprocess.TimeoutExpired("assemble.py", 900)
            if code:
                app.logger.error("KAC job %s failed: %s", key, "\n".join(tail))
                detail = tail[-1] if tail else ""
                if detail.startswith("Ошибка: ") and str(folder) not in detail:
                    raise ValueError(detail.removeprefix("Ошибка: "))
                raise RuntimeError("KAC export failed")
            next(result.glob("*.pdf")).replace(folder / "result.pdf")
            with (result / "Страницы КП.csv").open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.reader(stream, delimiter=";"))[1:]
            with ZipFile(folder / "images.zip", "w") as archive:
                for section, *_, image_path in rows:
                    path = result / image_path
                    archive.write(path, f"{sections[int(section)]}/{path.name}")
            status = {"status": "done", "stage": "done", "progress": 1.0,
                      "pages": len(rows), "sections": len(sections)}
        except ValueError as error:
            status = {"status": "error", "error": str(error)}
        except subprocess.TimeoutExpired:
            status = {"status": "error", "error": "Сборка не завершилась за 15 минут."}
        except Exception:
            app.logger.exception("Failed to assemble KAC job %s", key)
            status = {"status": "error", "error": "Не удалось собрать документ. Проверьте шаблон и журнал сервиса КАЦ."}
        finally:
            try:
                (folder / "source.docx").unlink(missing_ok=True)
            except OSError:
                app.logger.exception("Could not remove KAC source")
            for name in ("offers", "result"):
                shutil.rmtree(folder / name, ignore_errors=True)
            with lock:
                jobs[key].update(status, finished=time.time())
                info = dict(jobs[key])
            audit_event("build", info.get("audit_user"), app.logger,
                        user_name=info.get("audit_name"),
                        status=status["status"], pages=status.get("pages"),
                        duration_ms=int((time.time() - info.get("started", time.time())) * 1000),
                        error=status.get("error"),
                        details={"sections": status.get("sections")} if status.get("sections") else None)

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = (
            "public, max-age=31536000, immutable"
            if request.path.startswith("/ui/assets/")
            else "no-store"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; object-src 'none'; frame-ancestors 'self'; base-uri 'none'"
        )
        return response

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error="За один раз можно загрузить до 500 PDF общим объёмом до 200 МБ вместе с DOCX."), 413

    @app.get("/")
    def index():
        return send_file(UI / "index.html")

    @app.get("/ui/<path:filename>")
    def ui_assets(filename):
        return send_from_directory(UI, filename)

    @app.before_request
    def forward_to_worker():
        if not upstream or not upstream.hostname:
            return None
        if not re.fullmatch(r"/api/(?:health|jobs(?:/[a-f0-9]{32}(?:/pdf|/zip)?)?)", request.path):
            return None
        connection_type = HTTPSConnection if upstream.scheme == "https" else HTTPConnection
        connection = connection_type(upstream.hostname, upstream.port, timeout=60)
        headers = {key: request.headers[key] for key in ("Content-Type", "Content-Length", "Cookie")
                   if key in request.headers}
        try:
            connection.request(request.method, "/kac" + request.path,
                               body=request.stream if request.method == "POST" else None,
                               headers=headers)
            remote = connection.getresponse()
        except (OSError, HTTPException):
            connection.close()
            app.logger.exception("Could not reach the Windows KAC worker")
            return jsonify(error="Windows-обработчик КАЦ недоступен."), 502
        response_headers = [(key, value) for key, value in remote.getheaders()
                            if key.lower() in {"content-type", "content-length",
                                               "content-disposition", "set-cookie"}]

        def chunks():
            try:
                yield from iter(lambda: remote.read(64 * 1024), b"")
            finally:
                connection.close()

        response = Response(chunks(), status=remote.status, headers=response_headers)
        response.call_on_close(connection.close)
        return response

    @app.get("/api/health")
    def health():
        return {"available": available, "template": template.name if template and template.is_file() else None}

    @app.post("/api/jobs")
    def upload():
        if not available:
            return jsonify(error="Обработчик КАЦ недоступен."), 503
        document = request.files.get("docx")
        offers = request.files.getlist("offer")
        template_exists = template is not None and template.is_file()
        if not offers or (document and not document.filename.lower().endswith(".docx")) or (
            not document and not template_exists
        ):
            return jsonify(error="Выберите основной DOCX и папки с PDF."), 400
        sections = {}
        section_paths = {}
        files = {}
        try:
            for offer in offers:
                section, directory, name, relative_folder = upload_path(offer.filename)
                if section_paths.setdefault(section, relative_folder) != relative_folder:
                    raise ValueError(f"Загружены две папки для раздела {section}.")
                sections[section] = directory
                if (section, name.casefold()) in files:
                    raise ValueError(f"В разделе {section} повторяется файл «{name}».")
                files[section, name.casefold()] = (name, offer)
        except ValueError as error:
            return jsonify(error=str(error)), 400
        owner = session.setdefault("owner", secrets.token_hex(16))
        key = secrets.token_hex(16)
        folder = root / key
        with lock:
            if sum("finished" not in job for job in jobs.values()) >= 4:
                return jsonify(error="Очередь заполнена. Повторите после завершения сборки."), 429
            jobs[key] = {"owner": owner, "status": "queued", "stage": "queued", "progress": 0.05,
                         "audit_user": request.headers.get("X-Auth-User", ""),
                         "audit_name": request.headers.get("X-Auth-Name", ""),
                         "started": time.time()}
        try:
            folder.mkdir()
            source = folder / "source.docx"
            if document:
                document.save(source)
            else:
                shutil.copyfile(template, source)
            for (section, _), (name, offer) in files.items():
                directory = folder / "offers" / sections[section]
                directory.mkdir(parents=True, exist_ok=True)
                offer.save(directory / name)
            pool.submit(run_job, key, sections)
        except Exception:
            with lock:
                jobs.pop(key, None)
            shutil.rmtree(folder, ignore_errors=True)
            app.logger.exception("Could not stage KAC inputs")
            return jsonify(error="Не удалось сохранить загруженные файлы."), 500
        return jsonify(id=key), 202

    @app.get("/api/jobs/<key>")
    @app.get("/api/jobs/<key>/<kind>")
    def job_result(key, kind=None):
        with lock:
            job = jobs.get(key)
            if job and job["owner"] == session.get("owner"):
                if kind is None:
                    return {k: v for k, v in job.items() if k not in {"owner", "finished", "audit_user", "audit_name", "started"}}
                if job["status"] == "done" and kind in DOWNLOADS:
                    audit_event("download", job.get("audit_user") or request.headers.get("X-Auth-User", ""),
                                app.logger, user_name=job.get("audit_name") or request.headers.get("X-Auth-Name", ""),
                                details={"kind": kind})
                    file, name = DOWNLOADS[kind]
                    inline = kind == "pdf" and request.args.get("inline") == "1"
                    return send_file(root / key / file, as_attachment=not inline, download_name=name)
        return jsonify(error="Задание недоступно. Загрузите файлы заново."), 404

    return app
