from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    main._hits.clear()


def payload(**kw):
    base = {"event_type": "birthday", "guests": 40, "budget": 60000, "city": "Indore",
            "event_date": (date.today() + timedelta(days=60)).isoformat(), "preferences": "superhero theme"}
    return {**base, **kw}


def test_plan_ok_offline():
    r = client.post("/api/plan", json=payload())
    assert r.status_code == 200
    j = r.json()
    assert {"budget", "timeline", "vendors", "suggestions"} <= j.keys()
    assert j["suggestions"]["source"] == "built-in"


@pytest.mark.parametrize("bad", [{"guests": 0}, {"budget": 10}, {"event_type": "party"},
                                 {"event_date": "2020-01-01"}, {"city": "x"}])
def test_validation_rejects(bad):
    assert client.post("/api/plan", json=payload(**bad)).status_code == 422


def test_sanitizes_markup():
    r = client.post("/api/plan", json=payload(preferences="<script>alert(1)</script> cake"))
    assert r.status_code == 200
    assert "<" not in str(r.json()["suggestions"])


def test_rate_limit():
    codes = [client.post("/api/plan", json=payload()).status_code for _ in range(22)]
    assert codes.count(429) >= 1


def test_security_headers_and_health():
    r = client.get("/api/health")
    assert r.json() == {"status": "ok"} and r.headers["X-Content-Type-Options"] == "nosniff"
