"""Serve the gesn-match application at its portal path or directly."""

from argparse import ArgumentParser

from waitress import serve
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from app import apply_schema, create_match_app


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    apply_schema()
    application = DispatcherMiddleware(NotFound(), {"/gesn-match": create_match_app()})
    serve(application, host=args.host, port=args.port, threads=8,
          max_request_body_size=200 * 1024 * 1024, channel_timeout=360)
