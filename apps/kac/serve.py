"""Serve the KAC application at its portal path or directly at /kac/."""

from argparse import ArgumentParser
import sys

from waitress import serve
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from app import create_kac_app


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    application = DispatcherMiddleware(NotFound(), {"/kac": create_kac_app()})
    serve(application, host=args.host, port=args.port, threads=8,
          max_request_body_size=sys.maxsize, channel_timeout=360)
