"""FastAPI application initialization and middleware configuration."""

from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from .config import CSP_POLICY, PUBLIC_DIR
from .routes import limiter, router

load_dotenv()

app = FastAPI(title="Celebration & Event Planner")
app.include_router(router)

# Compatibility alias for existing test fixtures
_hits = limiter._hits


@app.middleware("http")
async def security_headers(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """Inject strict security headers and CSP policy into every HTTP response.

    Args:
        request: The incoming HTTP request.
        call_next: The next ASGI middleware/handler in chain.

    Returns:
        HTTP response with attached security headers.
    """
    resp: Response = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = CSP_POLICY
    return resp


if PUBLIC_DIR.is_dir():
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")
