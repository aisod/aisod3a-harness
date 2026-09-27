"""
AISOD 3A Harness — Vercel serverless entry point.

Vercel's Python runtime expects functions in an `api/` directory.
This wrapper imports the harness app and serves it via Mangum
(ASGI-to-serverless adapter), which Vercel's Python builder supports
through the @vercel/python builder.
"""

import api_server

app = api_server.app


def handler(environ, start_response):
    """WSGI handler that Vercel's Python runtime calls."""
    try:
        from mangum import Mangum

        handler_instance = Mangum(app, lifespan="off")
        return handler_instance(environ, start_response)
    except ImportError:
        from io import BytesIO

        status = "200 OK"
        headers = [("Content-Type", "application/json")]
        start_response(status, headers)
        body = b'{"detail":"Mangum not installed - add mangum to requirements.txt"}'
        return [body]


# Vercel also supports ASGI directly if the function exports an `app` object.
# Some Vercel Python runtimes look for `app` as an ASGI application.
asgi_app = app
