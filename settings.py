import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


# LLM: "gemini" (GOOGLE_API_KEY) or "groq" (GROQ_API_KEY); LLM_MODEL overrides the provider's default model
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or None

# Pipeline
MAX_SOURCES = _int("MAX_SOURCES", 6)
RESULTS_PER_QUESTION = _int("RESULTS_PER_QUESTION", 3)
MAX_REVISIONS = _int("MAX_REVISIONS", 2)
PASS_SCORE = _float("PASS_SCORE", 8.0)
MAX_SCRAPE_CHARS = _int("MAX_SCRAPE_CHARS", 6000)

# Server
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
MAX_TOPIC_CHARS = _int("MAX_TOPIC_CHARS", 300)
RATE_LIMIT_PER_MINUTE = _int("RATE_LIMIT_PER_MINUTE", 5)
MAX_CONCURRENT_RUNS = _int("MAX_CONCURRENT_RUNS", 2)
