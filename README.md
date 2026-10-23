# Celebration & Event Planner

A GenAI planning assistant for weddings, birthdays and community events. Enter event type, guests, budget (INR), city, date and preferences. You get a budget split, a dated timeline, a vendor checklist and personalised ideas.

## How it works
- **Rule engine (`app/planner.py`)**: budget split per event type, timeline scaled to the time left (rush mode when short), vendor checklist, and a per-guest budget warning. Deterministic and unit tested.
- **Gemini (`app/llm.py`)**: adds personalised ideas and tips as JSON. If the key is missing or the call fails, the app falls back to built-in suggestions, so it always works.
- **API (`app/main.py`)**: FastAPI, `POST /api/plan`.
- **UI (`static/`)**: plain HTML/CSS/JS, no build step.

## Run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY (optional)
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. Run tests with `pytest`.

## Security
Key only in `.env` (git-ignored); Pydantic validation with strict limits; markup stripped from text; user notes wrapped as untrusted data in the prompt; per-IP rate limiting; CSP and security headers; UI renders with `textContent` (no HTML injection).

## Efficiency
Rule-based logic runs instantly with no API call; Gemini responses are cached (LRU) and use JSON mode.

## Accessibility
Semantic landmarks, labelled fields with hints, skip link, live status, `role=alert` warnings, table captions and scoped headers, visible focus, light/dark and reduced-motion support, print styles.

## Testing
`pytest` covers budget math, timeline rush logic, validation, sanitization, rate limiting and headers.
