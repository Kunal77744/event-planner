"""Integration and API endpoint tests."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import main, routes
from app.ratelimit import RateLimiter

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to ensure offline behavior and rate limit clearing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    main._hits.clear()


def payload(**kw: Any) -> dict[str, Any]:
    """Helper to construct valid base plan request payloads."""
    base: dict[str, Any] = {
        "event_type": "birthday",
        "guests": 40,
        "budget": 60000,
        "city": "Indore",
        "event_date": (date.today() + timedelta(days=60)).isoformat(),
        "preferences": "superhero theme",
    }
    return {**base, **kw}


def test_plan_ok_offline() -> None:
    """Test standard plan generation with offline suggestions."""
    r = client.post("/api/plan", json=payload())
    assert r.status_code == 200
    j = r.json()
    assert {"budget", "timeline", "vendors", "suggestions"} <= j.keys()
    assert j["suggestions"]["source"] == "built-in"


@pytest.mark.parametrize(
    "bad",
    [
        {"guests": 0},
        {"budget": 10},
        {"event_type": "party"},
        {"event_date": "2020-01-01"},
        {"city": "x"},
    ],
)
def test_validation_rejects(bad: dict[str, Any]) -> None:
    """Test validation reject on invalid input payloads."""
    assert client.post("/api/plan", json=payload(**bad)).status_code == 422


def test_sanitizes_markup() -> None:
    """Verify HTML tags and scripts are stripped from user preferences."""
    r = client.post(
        "/api/plan",
        json=payload(preferences="<script>alert(1)</script> cake"),
    )
    assert r.status_code == 200
    assert "<" not in str(r.json()["suggestions"])


def test_rate_limit() -> None:
    """Test in-memory rate limiter triggers HTTP 429 when threshold exceeded."""
    codes = [client.post("/api/plan", json=payload()).status_code for _ in range(22)]
    assert codes.count(429) >= 1


def test_security_headers_and_health() -> None:
    """Test health check response and mandatory security headers."""
    r = client.get("/api/health")
    assert r.json() == {"status": "ok"}
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in r.headers


def test_root_index_and_static_app() -> None:
    """Verify index page and static JavaScript asset loading."""
    r_index = client.get("/")
    assert r_index.status_code == 200
    assert "Celebration &amp; Event Planner" in r_index.text

    r_js = client.get("/public/app.js")
    assert r_js.status_code == 200
    assert "plan-form" in r_js.text


def test_root_index_missing_raises_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 404 is returned if index.html does not exist."""
    monkeypatch.setattr(routes, "PUBLIC_DIR", Path("/nonexistent/directory"))
    r = client.get("/")
    assert r.status_code == 404
    assert r.json()["detail"] == "index.html not found"


def test_plan_gemini_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test plan generation when Gemini API returns valid structured response."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-valid-key")
    mock_data = json.dumps({"ideas": ["Custom Idea 1", "Custom Idea 2"], "tips": ["Custom Tip 1"]})
    monkeypatch.setattr("app.llm._cached", lambda *args: mock_data)

    r = client.post("/api/plan", json=payload())
    assert r.status_code == 200
    j = r.json()
    assert j["suggestions"]["source"] == "gemini"
    assert "Custom Idea 1" in j["suggestions"]["ideas"]


def test_plan_gemini_fallback_on_invalid_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test graceful fallback when Gemini response is empty or malformed."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-valid-key")
    monkeypatch.setattr("app.llm._cached", lambda *args: json.dumps({"ideas": [], "tips": []}))

    r = client.post("/api/plan", json=payload())
    assert r.status_code == 200
    j = r.json()
    assert j["suggestions"]["source"] == "built-in"


def test_rate_limiter_window_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that RateLimiter allows requests again after sliding window expires."""
    limiter = RateLimiter(limit=1, window=10)
    current_time = 1000.0
    monkeypatch.setattr("time.monotonic", lambda: current_time)

    assert limiter.check("client-a") is True
    assert limiter.check("client-a") is False

    # Advance time beyond the 10-second window
    current_time += 11.0
    assert limiter.check("client-a") is True

    # Test clear resets all tracked state
    limiter.clear()
    assert len(limiter._hits) == 0
