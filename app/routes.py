"""API endpoints and routes for Celebration & Event Planner."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

from .config import PUBLIC_DIR
from .llm import get_ideas
from .planner import build_plan
from .ratelimit import RateLimiter
from .refine import apply_message
from .schemas import PlanRequest

router = APIRouter()
limiter = RateLimiter()


def _enforce_rate_limit(request: Request) -> None:
    """Enforce sliding window rate limit on request client IP.

    Args:
        request: The incoming FastAPI request.

    Raises:
        HTTPException: 429 status code if client exceeded rate limit.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute.")


class RefineRequest(BaseModel):
    """Schema for chat-based plan refinement requests."""

    plan: PlanRequest
    message: str = Field(min_length=2, max_length=300)


@router.post("/api/plan")
def create_plan(req: PlanRequest, request: Request) -> dict[str, Any]:
    """Generate budget breakdown, timeline, vendors, and personalized ideas.

    Args:
        req: Validated plan request parameters.
        request: Raw HTTP request for rate limiting.

    Returns:
        Structured plan dictionary.
    """
    _enforce_rate_limit(request)
    plan: dict[str, Any] = build_plan(req.event_type, req.guests, req.budget, req.event_date)
    plan["suggestions"] = get_ideas(
        req.event_type,
        req.guests,
        req.budget,
        req.city,
        req.event_date,
        req.preferences,
    )
    return plan


@router.post("/api/refine")
def refine_plan(req: RefineRequest, request: Request) -> dict[str, Any]:
    """Update an existing plan via conversational message; recalculates numbers by rules.

    Args:
        req: Existing plan and refinement message.
        request: Raw HTTP request for rate limiting.

    Returns:
        Updated structured plan dictionary with recorded change log.
    """
    _enforce_rate_limit(request)
    data, changes = apply_message(req.plan, req.message)
    try:
        new_plan = PlanRequest(**data)
    except ValidationError as exc:
        msgs = "; ".join(e["msg"] for e in exc.errors())
        raise HTTPException(status_code=422, detail=f"That change is not allowed: {msgs}") from exc

    plan: dict[str, Any] = build_plan(
        new_plan.event_type, new_plan.guests, new_plan.budget, new_plan.event_date
    )
    plan["suggestions"] = get_ideas(
        new_plan.event_type,
        new_plan.guests,
        new_plan.budget,
        new_plan.city,
        new_plan.event_date,
        new_plan.preferences,
    )
    plan["request"] = new_plan.model_dump(mode="json")
    plan["changes"] = changes
    return plan


@router.get("/api/health")
def health() -> dict[str, str]:
    """Health check endpoint for platform monitoring.

    Returns:
        Status dictionary.
    """
    return {"status": "ok"}


@router.get("/")
def index() -> FileResponse:
    """Serve single-page application frontend.

    Returns:
        FileResponse serving index.html.

    Raises:
        HTTPException: 404 if index.html is missing.
    """
    index_path = PUBLIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)
