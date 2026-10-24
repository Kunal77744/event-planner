"""Application configuration constants."""

from pathlib import Path

# Paths
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
PUBLIC_DIR: Path = ROOT_DIR / "public"

# Rate limiting
RATE_LIMIT_MAX_REQUESTS: int = 20
RATE_LIMIT_WINDOW_SECONDS: int = 60

# LLM settings
DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
LRU_CACHE_MAX_SIZE: int = 128
MAX_IDEAS_COUNT: int = 6
MAX_TIPS_COUNT: int = 4

# Security headers
CSP_POLICY: str = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'"
