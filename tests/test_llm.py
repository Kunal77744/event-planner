"""Tests for Gemini LLM integration and offline fallback."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app import llm


def test_get_ideas_offline_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify built-in curated ideas are returned when no API key is set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = llm.get_ideas("wedding", 100, 500_000, "Jaipur", date.today(), "sunset ceremony")
    assert res["source"] == "built-in"
    assert len(res["ideas"]) >= 3
    assert any("sunset ceremony" in idea for idea in res["ideas"])


def test_get_ideas_with_gemini_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify structured ideas and tips returned when Gemini succeeds."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-key")
    llm._cached.cache_clear()

    mock_resp = MagicMock()
    mock_resp.text = (
        '{"ideas": ["Royal palace entry", "Folk dance"], '
        '"tips": ["Book heritage hall", "Local catering"]}'
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("google.genai.Client", return_value=mock_client):
        res = llm.get_ideas("wedding", 150, 800_000, "Udaipur", date.today(), "")
        assert res["source"] == "gemini"
        assert len(res["ideas"]) == 2
        assert "Royal palace entry" in res["ideas"]
        assert len(res["tips"]) == 2


def test_get_ideas_gemini_failure_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify graceful degradation when Gemini API call raises an exception."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-key")
    llm._cached.cache_clear()

    with patch("google.genai.Client", side_effect=RuntimeError("Quota exceeded")):
        res = llm.get_ideas("birthday", 50, 50_000, "Pune", date.today(), "")
        assert res["source"] == "built-in"
        assert len(res["ideas"]) >= 3


def test_get_ideas_gemini_empty_ideas_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fallback activates when Gemini returns empty ideas list."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-key")
    llm._cached.cache_clear()

    mock_resp = MagicMock()
    mock_resp.text = '{"ideas": [], "tips": []}'

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("google.genai.Client", return_value=mock_client):
        res = llm.get_ideas("community", 200, 100_000, "Delhi", date.today(), "")
        assert res["source"] == "built-in"
