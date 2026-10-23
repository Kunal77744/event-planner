"""Conversational refinement: turn a chat message into changes to the plan request.

Numbers are always recomputed by the rule engine (planner.py); this module only
interprets what the user asked for. Unmatched messages become preferences, which
personalise the Gemini ideas.
"""
from __future__ import annotations

import re

from .schemas import PlanRequest, clean_text

_DOWN = ("reduce", "decrease", "cut", "lower", "less", "kam", "drop")
_UP = ("increase", "raise", "more", "higher", "badha", "add")
_UNITS = {"k": 1_000, "lakh": 100_000, "lac": 100_000, "crore": 10_000_000}


def _amount(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|crore|k)?\b", text)
    if not m:
        return None
    return float(m.group(1)) * _UNITS.get(m.group(2) or "", 1)


def apply_message(req: PlanRequest, message: str) -> tuple[dict, list[str]]:
    """Return (updated request fields, human-readable list of changes)."""
    msg = clean_text(message).lower()
    data = req.model_dump(mode="json")
    changes: list[str] = []

    if "budget" in msg:
        pct = re.search(r"(\d+(?:\.\d+)?)\s*%", msg)
        if pct and any(w in msg for w in _DOWN + _UP):
            sign = -1 if any(w in msg for w in _DOWN) else 1
            data["budget"] = round(req.budget * (1 + sign * float(pct.group(1)) / 100))
            changes.append(f"Budget {'reduced' if sign < 0 else 'increased'} by {pct.group(1)}%")
        else:
            amt = _amount(msg.split("budget", 1)[1])
            if amt:
                data["budget"] = round(amt)
                changes.append(f"Budget set to Rs {round(amt):,}")

    g = re.search(r"(\d+)\s*(?:guests?|people|log|mehman)|(?:guests?|people)\D{0,15}(\d+)", msg)
    if g:
        data["guests"] = int(g.group(1) or g.group(2))
        changes.append(f"Guests set to {data['guests']}")

    if not changes:
        data["preferences"] = clean_text(f"{req.preferences} {message}")[-500:]
        changes.append("Added your request to preferences for new ideas")
    return data, changes
