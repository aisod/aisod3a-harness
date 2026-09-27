"""
AISOD 3A Harness — Vercel serverless entry point.

Vercel's Python runtime expects functions in an `api/` directory.
This wrapper imports the harness app and serves it via Mangum
(ASGI-to-serverless adapter), which Vercel's Python builder supports
through the @vercel/python builder.
"""

import os
import sys

# Ensure the project root is on the path so we can import the harness.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import the FastAPI app from the root module.
from api_server import app  # noqa: E402


def handler(environ, start_response):
    """WSGI handler that Vercel's Python runtime calls."""
    # Mangum converts ASGI (FastAPI) to WSGI for Vercel.
    try:
        from mangum import Mangum

        handler_instance = Mangum(app, lifespan="off")
        return handler_instance(environ, start_response)
    except ImportError:
        # Fallback: basic WSGI pass-through (not recommended for production).
        from io import BytesIO

        status = "200 OK"
        headers = [("Content-Type", "application/json")]
        start_response(status, headers)
        body = b'{"detail":"Mangum not installed - add mangum to requirements.txt"}'
        return [body]


# Vercel also supports ASGI directly if the function exports an `app` object.
# Some Vercel Python runtimes look for `app` as an ASGI application.
asgi_app = app
