"""FastAPI app: POST /api/plan and static frontend."""
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .llm import get_ideas  # noqa: E402
from .planner import build_plan  # noqa: E402
from .refine import apply_message  # noqa: E402
from .schemas import PlanRequest  # noqa: E402

PUBLIC = Path(__file__).resolve().parent.parent / "public"
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


class RefineRequest(BaseModel):
    plan: PlanRequest
    message: str = Field(min_length=2, max_length=300)


@app.post("/api/refine")
def refine_plan(req: RefineRequest, request: Request) -> dict:
    """Update an existing plan from a chat message; numbers are recomputed by rules."""
    _check_rate(request.client.host if request.client else "unknown")
    data, changes = apply_message(req.plan, req.message)
    try:
        new = PlanRequest(**data)
    except ValidationError as exc:
        msgs = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(422, f"That change is not allowed: {msgs}") from exc
    plan = build_plan(new.event_type, new.guests, new.budget, new.event_date)
    plan["suggestions"] = get_ideas(new.event_type, new.guests, new.budget,
                                    new.city, new.event_date, new.preferences)
    plan["request"] = new.model_dump(mode="json")
    plan["changes"] = changes
    return plan


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/")
def index():
    p = PUBLIC / "index.html"
    return FileResponse(p) if p.exists() else {"status": "ok"}


@app.get("/index.html")
def index_html():
    p = PUBLIC / "index.html"
    return FileResponse(p) if p.exists() else {"status": "ok"}


@app.get("/app.js")
def app_js():
    p = PUBLIC / "app.js"
    return FileResponse(p) if p.exists() else {"status": "ok"}


if PUBLIC.is_dir():
    app.mount("/public", StaticFiles(directory=PUBLIC), name="public")


