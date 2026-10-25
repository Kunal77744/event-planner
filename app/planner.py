"""Deterministic planning engine implementing Strategy Pattern for event types.

Rules and domain logic live here (not in the LLM) so results are predictable,
transparent, and testable. The LLM only adds personalised suggestions on top.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from enum import StrEnum
from typing import Any


class EventType(StrEnum):
    """Supported celebration and event domain types."""

    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    COMMUNITY = "community"


class EventStrategy(ABC):
    """Abstract Strategy defining rules, thresholds, and checklists per event type."""

    @property
    @abstractmethod
    def event_type(self) -> EventType:
        """Domain event type identifier."""
        ...

    @property
    @abstractmethod
    def budget_rules(self) -> dict[str, float]:
        """Categorical budget allocation ratios summing to 1.0."""
        ...

    @property
    @abstractmethod
    def min_per_guest(self) -> int:
        """Typical minimum expenditure per guest in INR."""
        ...

    @property
    @abstractmethod
    def tasks(self) -> list[tuple[int, str]]:
        """Preparation milestone tuples of (days_before_event, task_description)."""
        ...

    @property
    @abstractmethod
    def vendors(self) -> list[str]:
        """Recommended vendor categories checklist."""
        ...

    @property
    @abstractmethod
    def base_ideas(self) -> list[str]:
        """Curated baseline creative concepts."""
        ...


class WeddingStrategy(EventStrategy):
    """Planning strategy for wedding celebrations."""

    @property
    def event_type(self) -> EventType:
        return EventType.WEDDING

    @property
    def budget_rules(self) -> dict[str, float]:
        return {
            "Venue": 0.25,
            "Catering": 0.30,
            "Decor & Flowers": 0.12,
            "Photography & Video": 0.10,
            "Attire & Beauty": 0.08,
            "Entertainment": 0.05,
            "Invitations & Gifts": 0.03,
            "Contingency": 0.07,
        }

    @property
    def min_per_guest(self) -> int:
        return 1500

    @property
    def tasks(self) -> list[tuple[int, str]]:
        return [
            (300, "Fix budget and finalise guest list"),
            (270, "Book venue and date"),
            (240, "Book photographer and caterer"),
            (180, "Shop for attire, book makeup"),
            (120, "Send save-the-dates, book decorator"),
            (60, "Send invitations, finalise menu"),
            (30, "Confirm all vendors, plan seating"),
            (7, "Final headcount and payments"),
            (1, "Rehearsal and vendor briefing"),
        ]

    @property
    def vendors(self) -> list[str]:
        return [
            "Venue / banquet hall",
            "Caterer",
            "Decorator & florist",
            "Photographer & videographer",
            "Makeup artist",
            "DJ / band",
            "Priest / officiant",
            "Transport & accommodation",
            "Invitation printer",
        ]

    @property
    def base_ideas(self) -> list[str]:
        return [
            "Plan a sunset ceremony with a welcome drinks hour",
            "Add a live food counter featuring local specialities",
            "Create a memory wall with family photos",
        ]


class BirthdayStrategy(EventStrategy):
    """Planning strategy for birthday celebrations."""

    @property
    def event_type(self) -> EventType:
        return EventType.BIRTHDAY

    @property
    def budget_rules(self) -> dict[str, float]:
        return {
            "Venue": 0.15,
            "Catering & Cake": 0.35,
            "Decor": 0.18,
            "Entertainment": 0.17,
            "Photography": 0.05,
            "Return Gifts": 0.05,
            "Contingency": 0.05,
        }

    @property
    def min_per_guest(self) -> int:
        return 500

    @property
    def tasks(self) -> list[tuple[int, str]]:
        return [
            (45, "Set budget and guest list"),
            (35, "Book venue"),
            (28, "Pick theme, order cake"),
            (21, "Send invitations"),
            (14, "Book entertainment and decor"),
            (7, "Confirm RSVPs and buy return gifts"),
            (1, "Confirm vendors, prep the venue"),
        ]

    @property
    def vendors(self) -> list[str]:
        return [
            "Venue / party space",
            "Caterer or bakery",
            "Decorator",
            "Entertainer / host",
            "Photographer",
        ]

    @property
    def base_ideas(self) -> list[str]:
        return [
            "Pick one theme and build decor, cake and games around it",
            "Run a mini treasure hunt or quiz",
            "Set up a DIY photo corner",
        ]


class CommunityStrategy(EventStrategy):
    """Planning strategy for community and cultural gatherings."""

    @property
    def event_type(self) -> EventType:
        return EventType.COMMUNITY

    @property
    def budget_rules(self) -> dict[str, float]:
        return {
            "Venue & Permits": 0.20,
            "Food & Refreshments": 0.28,
            "Stage, Sound & Lighting": 0.17,
            "Publicity": 0.10,
            "Volunteers & Safety": 0.10,
            "Activities": 0.08,
            "Contingency": 0.07,
        }

    @property
    def min_per_guest(self) -> int:
        return 150

    @property
    def tasks(self) -> list[tuple[int, str]]:
        return [
            (90, "Define goal, budget and committee"),
            (75, "Get permissions and permits"),
            (60, "Book venue, sound and stage"),
            (45, "Recruit volunteers, find sponsors"),
            (30, "Start publicity"),
            (14, "Confirm food and safety plan"),
            (7, "Run volunteer briefing"),
            (1, "Set up venue, test equipment"),
        ]

    @property
    def vendors(self) -> list[str]:
        return [
            "Venue owner / local authority",
            "Caterer",
            "Sound & lighting",
            "Printer (banners, flyers)",
            "First-aid / security",
            "Cleaning crew",
        ]

    @property
    def base_ideas(self) -> list[str]:
        return [
            "Open with a short cultural performance to draw crowds",
            "Use a sign-up desk to track attendance",
            "Add a local food stall zone",
        ]


# Strategy registry mapping
_STRATEGIES: dict[str, EventStrategy] = {
    EventType.WEDDING.value: WeddingStrategy(),
    EventType.BIRTHDAY.value: BirthdayStrategy(),
    EventType.COMMUNITY.value: CommunityStrategy(),
}


def get_strategy(event_type: str | EventType) -> EventStrategy:
    """Retrieve planning strategy instance for the given event type.

    Args:
        event_type: String or EventType enum value.

    Returns:
        Concrete EventStrategy implementation.

    Raises:
        KeyError: If the event type is unsupported.
    """
    key = event_type.value if isinstance(event_type, EventType) else str(event_type).lower()
    if key not in _STRATEGIES:
        raise KeyError(f"Unsupported event type: '{event_type}'")
    return _STRATEGIES[key]


# Backwards compatibility aliases for existing tests and external consumers
BUDGET_RULES: dict[str, dict[str, float]] = {
    etype: strat.budget_rules for etype, strat in _STRATEGIES.items()
}
TASKS: dict[str, list[tuple[int, str]]] = {
    etype: strat.tasks for etype, strat in _STRATEGIES.items()
}
VENDORS: dict[str, list[str]] = {etype: strat.vendors for etype, strat in _STRATEGIES.items()}


def budget_breakdown(event_type: str, budget: float, guests: int) -> dict[str, Any]:
    """Calculate categorical budget breakdown and per-guest metrics.

    Args:
        event_type: Type of event ("wedding", "birthday", or "community").
        budget: Total allocated budget in INR.
        guests: Expected guest count.

    Returns:
        Dictionary containing itemized categories, per-guest cost, and warnings.
    """
    strategy = get_strategy(event_type)
    items = [
        {"category": c, "percent": round(p * 100), "amount": round(budget * p)}
        for c, p in strategy.budget_rules.items()
    ]
    per_guest = round(budget / guests)
    min_pg = strategy.min_per_guest
    warning = None
    if per_guest < min_pg:
        warning = (
            f"Budget works out to Rs {per_guest} per guest, below the typical "
            f"minimum of Rs {min_pg}. Consider fewer guests or a larger budget."
        )
    return {"items": items, "per_guest": per_guest, "warning": warning}


def timeline(event_type: str, event_date: date, today: date | None = None) -> dict[str, Any]:
    """Generate dated event preparation milestones, adjusting for rush mode.

    Args:
        event_type: Type of event.
        event_date: Target event date.
        today: Reference base date (defaults to date.today()).

    Returns:
        Timeline structure with milestone tasks, due dates, and lead days.
    """
    strategy = get_strategy(event_type)
    today = today or date.today()
    lead = (event_date - today).days
    tasks = strategy.tasks
    full = tasks[0][0]
    rush = lead < full
    scale = lead / full if rush else 1.0
    steps = []
    for days_before, task in tasks:
        d = max(1, round(days_before * scale)) if days_before > 1 else 1
        steps.append(
            {
                "due": (event_date - timedelta(days=d)).isoformat(),
                "days_before": d,
                "task": task,
            }
        )
    note = None
    if rush:
        note = (
            f"Only {lead} days left; a typical {event_type} needs {full}. "
            "Tasks are compressed, so book venue and caterer first."
        )
    return {"lead_days": lead, "rush": rush, "note": note, "steps": steps}


def vendor_checklist(event_type: str) -> list[str]:
    """Retrieve recommended vendor category checklist for event type.

    Args:
        event_type: Type of event.

    Returns:
        List of vendor roles/categories.
    """
    return list(get_strategy(event_type).vendors)


def fallback_ideas(event_type: str, city: str, preferences: str) -> dict[str, Any]:
    """Generate deterministic curated ideas and city tips without LLM dependency.

    Args:
        event_type: Type of event.
        city: Event hosting city.
        preferences: Optional user notes or preferences.

    Returns:
        Dictionary containing ideas, tips, and source designation.
    """
    strategy = get_strategy(event_type)
    base = list(strategy.base_ideas)
    if preferences:
        base.append(f"Tailor the programme to your note: {preferences[:100]}")
    return {
        "ideas": base,
        "tips": [
            f"Visit 2-3 venues in {city} before booking.",
            "Get written quotes from at least 3 vendors.",
        ],
        "source": "built-in",
    }


def build_plan(event_type: str, guests: int, budget: float, event_date: date) -> dict[str, Any]:
    """Assemble complete event plan combining budget, timeline, and vendors.

    Args:
        event_type: Type of event.
        guests: Guest count.
        budget: Total budget in INR.
        event_date: Event date.

    Returns:
        Consolidated plan structure.
    """
    return {
        "budget": budget_breakdown(event_type, budget, guests),
        "timeline": timeline(event_type, event_date),
        "vendors": vendor_checklist(event_type),
    }
