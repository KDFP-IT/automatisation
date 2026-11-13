from waitress import serve
from werkzeug.exceptions import NotFound
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from webapp.app import create_app


if __name__ == "__main__":
    app = create_app({
        "PORTAL_EMBEDDED": True,
        "SESSION_COOKIE_NAME": "portal_bookmarks",
        "SESSION_COOKIE_PATH": "/bookmarks/",
    })
    application = DispatcherMiddleware(NotFound(), {"/bookmarks": app})
    serve(application, host="0.0.0.0", port=8080, threads=8,
          max_request_body_size=200 * 1024 * 1024, channel_timeout=360)
