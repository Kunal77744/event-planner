from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import main
from app.refine import apply_message
from app.schemas import PlanRequest

client = TestClient(main.app)


def base(**kw):
    d = {"event_type": "wedding", "guests": 100, "budget": 500000, "city": "Indore",
         "event_date": (date.today() + timedelta(days=200)).isoformat(), "preferences": ""}
    return {**d, **kw}


def test_budget_percent_down():
    data, ch = apply_message(PlanRequest(**base()), "reduce budget by 20%")
    assert data["budget"] == 400000 and "reduced" in ch[0]


def test_budget_percent_up():
    assert apply_message(PlanRequest(**base()), "increase the budget by 10%")[0]["budget"] == 550000


def test_budget_absolute_lakh():
    assert apply_message(PlanRequest(**base()), "set budget to 8 lakh")[0]["budget"] == 800000


def test_guests_change():
    assert apply_message(PlanRequest(**base()), "we now have 150 guests")[0]["guests"] == 150


def test_unmatched_becomes_preference():
    data, _ = apply_message(PlanRequest(**base()), "outdoor with vegetarian menu")
    assert "vegetarian" in data["preferences"]


def test_refine_endpoint_recomputes(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    main._hits.clear()
    r = client.post("/api/refine", json={"plan": base(), "message": "reduce budget by 50%"})
    assert r.status_code == 200
    j = r.json()
    assert j["request"]["budget"] == 250000 and j["budget"]["items"][0]["amount"] == 62500
    assert j["changes"]


def test_refine_rejects_invalid_result(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    main._hits.clear()
    r = client.post("/api/refine", json={"plan": base(budget=6000), "message": "reduce budget by 90%"})
    assert r.status_code == 422
