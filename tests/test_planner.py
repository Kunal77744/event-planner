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


def test_strategies_properties() -> None:
    """Verify concrete strategy properties and event types."""
    for etype in planner.EventType:
        strat = planner.get_strategy(etype)
        assert strat.event_type == etype
        assert strat.min_per_guest > 0
        assert len(strat.tasks) > 0
        assert len(strat.vendors) > 0
        assert len(strat.base_ideas) > 0


def test_get_strategy_invalid() -> None:
    """Verify KeyError is raised for unsupported event type."""
    with pytest.raises(KeyError, match="Unsupported event type"):
        planner.get_strategy("conference")


def test_fallback_ideas_with_and_without_prefs() -> None:
    """Verify fallback_ideas output format and preference incorporation."""
    res1 = planner.fallback_ideas("birthday", "Mumbai", "")
    assert res1["source"] == "built-in"
    assert len(res1["ideas"]) >= 3
    assert len(res1["tips"]) == 2

    res2 = planner.fallback_ideas("community", "Delhi", "Eco-friendly theme")
    assert any("Eco-friendly" in idea for idea in res2["ideas"])


def test_build_plan_consolidated() -> None:
    """Verify build_plan combines budget, timeline, and vendors accurately."""
    res = planner.build_plan("wedding", 100, 500_000, date.today() + timedelta(days=60))
    assert "budget" in res
    assert "timeline" in res
    assert "vendors" in res
    assert res["budget"]["per_guest"] == 5000
    assert len(res["timeline"]["steps"]) > 0
    assert len(res["vendors"]) > 0
