"""Tests for deterministic event planner engine."""

from datetime import date, timedelta

import pytest

from app import planner


@pytest.mark.parametrize("etype", list(planner.BUDGET_RULES))
def test_budget_rules_sum_to_one(etype: str) -> None:
    """Verify categorical budget ratios sum up to 1.0."""
    assert sum(planner.BUDGET_RULES[etype].values()) == pytest.approx(1.0)


def test_budget_amounts_match_total() -> None:
    """Verify calculated budget amounts sum up to total specified budget."""
    r = planner.budget_breakdown("wedding", 1_000_000, 200)
    assert abs(sum(i["amount"] for i in r["items"]) - 1_000_000) <= 10
    assert r["per_guest"] == 5000 and r["warning"] is None


def test_low_budget_warns() -> None:
    """Verify warning triggers when per-guest budget falls below minimum threshold."""
    assert planner.budget_breakdown("wedding", 50_000, 300)["warning"]


def test_timeline_normal_not_rush() -> None:
    """Verify standard event timeline is scheduled when lead days are ample."""
    d = date.today() + timedelta(days=400)
    t = planner.timeline("wedding", d)
    assert not t["rush"] and t["steps"][0]["days_before"] == 300


def test_timeline_rush_compresses_and_stays_in_future() -> None:
    """Verify rush mode compresses preparation milestones into available lead time."""
    d = date.today() + timedelta(days=20)
    t = planner.timeline("wedding", d)
    assert t["rush"] and t["note"]
    assert all(s["days_before"] <= 20 for s in t["steps"])
    assert all(date.fromisoformat(s["due"]) >= date.today() for s in t["steps"])


def test_vendor_lists_nonempty() -> None:
    """Verify all event types provide non-empty vendor checklists."""
    for e in planner.VENDORS:
        assert planner.vendor_checklist(e)
