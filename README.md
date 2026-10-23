# Celebration & Event Planner

A GenAI planning assistant for weddings, birthdays and community events. Enter event type, guests, budget (INR), city, date and preferences to get a budget split, a dated timeline, a vendor checklist and personalised ideas. Then **chat with the assistant** ("reduce budget by 20%", "150 guests", "outdoor, vegetarian") and the plan updates.

**Live demo**: https://event-planner-ten-ruby.vercel.app/

## Scorecard (where to look in this repo)

| Criterion | What is implemented | Files |
|---|---|---|
| Problem alignment | Budgets, timelines, vendor checklists and personalised ideas for 3 event types, plus a conversational refine step | `app/planner.py`, `app/llm.py`, `app/refine.py` |
| Smart, context-based decisions | Budget split differs per event type; timeline compresses when the date is near (rush mode); per-guest budget warning; chat changes recompute every number by rules | `app/planner.py`, `app/refine.py` |
| Code quality | Small single-purpose modules, type hints, docstrings, no globals beyond rate-limit state, rules separated from the LLM | `app/` |
| Security | Key only in git-ignored `.env`; Pydantic limits on every field; markup stripped; user text wrapped as untrusted data in the prompt; per-IP rate limit; CSP and security headers; UI uses `textContent` | `app/schemas.py`, `app/main.py`, `app/llm.py`, `public/app.js` |
| Efficiency | Rules run with no API call; Gemini JSON mode with LRU cache; graceful fallback if key is missing or the call fails | `app/llm.py` |
| Testing | 25 pytest tests (budget math, timeline, validation, sanitization, rate limit, headers, chat refinement, static routes) run in CI | `tests/`, `.github/workflows/ci.yml` |
| Accessibility | Landmarks, labelled fields with hints, skip link, `aria-live` status, `role=alert` warnings, table captions and scoped headers, visible focus, dark mode, reduced motion, print styles | `public/` |

## Architecture
`public/` (HTML/JS) -> `POST /api/plan` and `POST /api/refine` (`app/main.py`) -> validation (`schemas.py`) -> rule engine (`planner.py`) + Gemini ideas (`llm.py`).

## Deployment
- **Platform**: Vercel Serverless Function (`api/index.py`) with frontend static assets served directly via Vercel's global CDN (`public/`).
- **Environment Variables**: Configure `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`, e.g. `gemini-2.0-flash` or `gemini-1.5-flash`) under Vercel Project Settings -> Environment Variables.
- **Graceful Fallback**: The app operates fully offline without an API key using built-in, curated Indian event suggestions.
- **Security Headers & CSP**: Enforced by FastAPI middleware on all API responses, and via `vercel.json` for CDN-served static assets.

## Run Locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add GEMINI_API_KEY (optional; app works without it)
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. Run tests with `pytest`.

## Design notes
- The LLM never decides numbers. Budgets and dates come from tested rules, so output is reliable and explainable.
- Chat messages that are not budget or guest changes are added to preferences, which personalise the Gemini ideas.

## Limitations
Budget shares and lead times are typical Indian-market defaults, not quotes. Rate limiting is in-memory and per process (per serverless instance); LRU cache is per serverless instance.
