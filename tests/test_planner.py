from datetime import date, timedelta

import pytest

from app import planner


@pytest.mark.parametrize("etype", list(planner.BUDGET_RULES))
def test_budget_rules_sum_to_one(etype):
    assert sum(planner.BUDGET_RULES[etype].values()) == pytest.approx(1.0)


def test_budget_amounts_match_total():
    r = planner.budget_breakdown("wedding", 1_000_000, 200)
    assert abs(sum(i["amount"] for i in r["items"]) - 1_000_000) <= 10
    assert r["per_guest"] == 5000 and r["warning"] is None


def test_low_budget_warns():
    assert planner.budget_breakdown("wedding", 50_000, 300)["warning"]


def test_timeline_normal_not_rush():
    d = date.today() + timedelta(days=400)
    t = planner.timeline("wedding", d)
    assert not t["rush"] and t["steps"][0]["days_before"] == 300


def test_timeline_rush_compresses_and_stays_in_future():
    d = date.today() + timedelta(days=20)
    t = planner.timeline("wedding", d)
    assert t["rush"] and t["note"]
    assert all(s["days_before"] <= 20 for s in t["steps"])
    assert all(date.fromisoformat(s["due"]) >= date.today() for s in t["steps"])


def test_vendor_lists_nonempty():
    for e in planner.VENDORS:
        assert planner.vendor_checklist(e)
