"""Start a persistent local server, install missing dependencies and open the UI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def running(url, service):
    try:
        with urllib.request.urlopen(url + "/api/health", timeout=1) as response:
            return json.load(response).get("service") == service
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main():
    parser = argparse.ArgumentParser(description="Запустить сервис «Лист» и открыть страницу")
    parser.add_argument("--port", type=int)
    parser.add_argument("--portal", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    port = args.port if args.port is not None else (8090 if args.portal else 8080)
    service = "automation-portal" if args.portal else "pdf-bookmarks"
    script = "portal.py" if args.portal else "app.py"
    url = f"http://127.0.0.1:{port}"
    if not running(url, service):
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(f"Порт {port} занят другим приложением. Укажите свободный порт через --port.")
        python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        env = dict(os.environ)
        if (ROOT / ".webdeps").is_dir():
            env["PYTHONPATH"] = str(ROOT / ".webdeps") + os.pathsep + env.get("PYTHONPATH", "")
        interpreter = str(python) if python.exists() else sys.executable
        imports = "import flask, waitress, pypdf, pypdfium2"
        if args.portal and os.name == "nt":
            imports += ", lxml.etree, PIL.Image"
        check = subprocess.run([interpreter, "-c", imports],
                               env=env, capture_output=True)
        if check.returncode:
            print("Первый запуск: создаём окружение и устанавливаем зависимости…", flush=True)
            if not python.exists():
                subprocess.check_call([sys.executable, "-m", "venv", str(ROOT / ".venv")])
            interpreter = str(python)
            subprocess.check_call([interpreter, "-m", "pip", "install", "-r", str(ROOT / "webapp/requirements.txt")])
        log_dir = ROOT / "webapp/data"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / ("portal.log" if args.portal else "server.log")
        with log_path.open("a", encoding="utf-8") as log:
            process = subprocess.Popen([interpreter, str(ROOT / "webapp" / script), "--host", args.host, "--port", str(port)],
                                       cwd=ROOT, env={**env, "PYTHONIOENCODING": "utf-8"},
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for _ in range(60):
            if running(url, service):
                break
            if process.poll() is not None:
                raise RuntimeError(f"Сервер не запустился. Подробности: {log_path}")
            time.sleep(0.25)
        else:
            process.terminate()
            process.wait(timeout=10)
            raise RuntimeError(f"Сервер не ответил. Подробности: {log_path}")
        (log_dir / ("portal.pid" if args.portal else "server.pid")).write_text(str(process.pid), encoding="ascii")
    print(f"Готово. Откройте {url}", flush=True)
    print("Сервер продолжит работать после закрытия этого окна.", flush=True)
    if not args.no_browser:
        webbrowser.open(url)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
