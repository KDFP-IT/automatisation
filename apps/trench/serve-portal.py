from pathlib import Path

from flask import send_from_directory
from waitress import serve
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from api.app import app


@app.get("/", defaults={"filename": "index.html"})
@app.get("/<path:filename>")
def frontend(filename):
    return send_from_directory(Path(__file__).resolve().parent / "dist", filename)


if __name__ == "__main__":
    application = DispatcherMiddleware(NotFound(), {"/trench": app})
    serve(application, host="0.0.0.0", port=8080, threads=8,
          max_request_body_size=200 * 1024 * 1024, channel_timeout=360)
