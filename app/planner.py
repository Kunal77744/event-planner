"""Deterministic planning engine: budget split, timeline, vendor checklist.

Rules live here (not in the LLM) so results are predictable and testable.
The LLM only adds personalised ideas on top.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# Share of budget per category. Each row sums to 1.0.
BUDGET_RULES: dict[str, dict[str, float]] = {
    "wedding": {
        "Venue": 0.25,
        "Catering": 0.30,
        "Decor & Flowers": 0.12,
        "Photography & Video": 0.10,
        "Attire & Beauty": 0.08,
        "Entertainment": 0.05,
        "Invitations & Gifts": 0.03,
        "Contingency": 0.07,
    },
    "birthday": {
        "Venue": 0.15,
        "Catering & Cake": 0.35,
        "Decor": 0.18,
        "Entertainment": 0.17,
        "Photography": 0.05,
        "Return Gifts": 0.05,
        "Contingency": 0.05,
    },
    "community": {
        "Venue & Permits": 0.20,
        "Food & Refreshments": 0.28,
        "Stage, Sound & Lighting": 0.17,
        "Publicity": 0.10,
        "Volunteers & Safety": 0.10,
        "Activities": 0.08,
        "Contingency": 0.07,
    },
}

# (days before event, task). Scaled down when lead time is short.
TASKS: dict[str, list[tuple[int, str]]] = {
    "wedding": [
        (300, "Fix budget and finalise guest list"),
        (270, "Book venue and date"),
        (240, "Book photographer and caterer"),
        (180, "Shop for attire, book makeup"),
        (120, "Send save-the-dates, book decorator"),
        (60, "Send invitations, finalise menu"),
        (30, "Confirm all vendors, plan seating"),
        (7, "Final headcount and payments"),
        (1, "Rehearsal and vendor briefing"),
    ],
    "birthday": [
        (45, "Set budget and guest list"),
        (35, "Book venue"),
        (28, "Pick theme, order cake"),
        (21, "Send invitations"),
        (14, "Book entertainment and decor"),
        (7, "Confirm RSVPs and buy return gifts"),
        (1, "Confirm vendors, prep the venue"),
    ],
    "community": [
        (90, "Define goal, budget and committee"),
        (75, "Get permissions and permits"),
        (60, "Book venue, sound and stage"),
        (45, "Recruit volunteers, find sponsors"),
        (30, "Start publicity"),
        (14, "Confirm food and safety plan"),
        (7, "Run volunteer briefing"),
        (1, "Set up venue, test equipment"),
    ],
}

VENDORS: dict[str, list[str]] = {
    "wedding": [
        "Venue / banquet hall",
        "Caterer",
        "Decorator & florist",
        "Photographer & videographer",
        "Makeup artist",
        "DJ / band",
        "Priest / officiant",
        "Transport & accommodation",
        "Invitation printer",
    ],
    "birthday": [
        "Venue / party space",
        "Caterer or bakery",
        "Decorator",
        "Entertainer / host",
        "Photographer",
    ],
    "community": [
        "Venue owner / local authority",
        "Caterer",
        "Sound & lighting",
        "Printer (banners, flyers)",
        "First-aid / security",
        "Cleaning crew",
    ],
}


def budget_breakdown(event_type: str, budget: float, guests: int) -> dict[str, Any]:
    """Calculate categorical budget breakdown and per-guest metrics.

    Args:
        event_type: Type of event ("wedding", "birthday", or "community").
        budget: Total allocated budget in INR.
        guests: Expected guest count.

    Returns:
        Dictionary containing itemized categories, per-guest cost, and warnings.
    """
    items = [
        {"category": c, "percent": round(p * 100), "amount": round(budget * p)}
        for c, p in BUDGET_RULES[event_type].items()
    ]
    per_guest = round(budget / guests)
    min_pg = {"wedding": 1500, "birthday": 500, "community": 150}[event_type]
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
    today = today or date.today()
    lead = (event_date - today).days
    tasks = TASKS[event_type]
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
    return list(VENDORS[event_type])


def fallback_ideas(event_type: str, city: str, preferences: str) -> dict[str, Any]:
    """Generate deterministic curated ideas and city tips without LLM dependency.

    Args:
        event_type: Type of event.
        city: Event hosting city.
        preferences: Optional user notes or preferences.

    Returns:
        Dictionary containing ideas, tips, and source designation.
    """
    base = {
        "wedding": [
            "Plan a sunset ceremony with a welcome drinks hour",
            "Add a live food counter featuring local specialities",
            "Create a memory wall with family photos",
        ],
        "birthday": [
            "Pick one theme and build decor, cake and games around it",
            "Run a mini treasure hunt or quiz",
            "Set up a DIY photo corner",
        ],
        "community": [
            "Open with a short cultural performance to draw crowds",
            "Use a sign-up desk to track attendance",
            "Add a local food stall zone",
        ],
    }[event_type]
    if preferences:
        base = base + [f"Tailor the programme to your note: {preferences[:100]}"]
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
