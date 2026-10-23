"""Request validation. All user input is validated and sanitized here."""
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def clean_text(value: str) -> str:
    """Strip control characters, angle brackets and collapse whitespace."""
    value = _CONTROL.sub("", value).replace("<", "").replace(">", "")
    return re.sub(r"\s+", " ", value).strip()


class PlanRequest(BaseModel):
    event_type: Literal["wedding", "birthday", "community"]
    guests: int = Field(ge=1, le=5000)
    budget: float = Field(ge=5000, le=100_000_000, description="Total budget in INR")
    city: str = Field(min_length=2, max_length=60)
    event_date: date
    preferences: str = Field(default="", max_length=500)

    @field_validator("city", "preferences")
    @classmethod
    def _sanitize(cls, v: str) -> str:
        return clean_text(v)

    @field_validator("event_date")
    @classmethod
    def _future(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError("event_date must be in the future")
        return v
