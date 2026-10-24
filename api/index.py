"""Vercel Serverless Function entrypoint."""

import sys
from pathlib import Path

# Ensure project root is in sys.path for serverless execution
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.main import app  # noqa: E402

__all__ = ["app"]
