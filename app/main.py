"""FastAPI app: POST /api/plan and static frontend."""
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .llm import get_ideas  # noqa: E402
from .planner import build_plan  # noqa: E402
from .schemas import PlanRequest  # noqa: E402

STATIC = Path(__file__).resolve().parent.parent / "static"
app = FastAPI(title="Celebration & Event Planner")

RATE_LIMIT, WINDOW = 20, 60  # requests per window (seconds) per client
_hits: dict[str, deque] = defaultdict(deque)


def _check_rate(client: str) -> None:
    now, q = time.monotonic(), _hits[client]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(429, "Too many requests. Please wait a minute.")
    q.append(now)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'"
    return resp


@app.post("/api/plan")
def create_plan(req: PlanRequest, request: Request) -> dict:
    _check_rate(request.client.host if request.client else "unknown")
    plan = build_plan(req.event_type, req.guests, req.budget, req.event_date)
    plan["suggestions"] = get_ideas(req.event_type, req.guests, req.budget,
                                    req.city, req.event_date, req.preferences)
    return plan


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
