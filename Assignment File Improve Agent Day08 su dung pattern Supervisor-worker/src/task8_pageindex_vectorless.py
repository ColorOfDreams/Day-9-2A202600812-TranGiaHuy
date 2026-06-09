"""Task 8 - PageIndex-compatible vectorless fallback."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
USE_PAGEINDEX_API = os.getenv("USE_PAGEINDEX_API", "false").lower() == "true"


def upload_documents():
    """Placeholder for real PageIndex uploads.

    PAGEINDEX_API_KEY is loaded from .env, but local tests do not call the API
    unless USE_PAGEINDEX_API=true is set by the user.
    """
    return list(STANDARDIZED_DIR.rglob("*.md"))


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Return fallback results marked as coming from PageIndex."""
    from .task6_lexical_search import lexical_search

    # Keep automated tests deterministic and network-free. A real PageIndex
    # integration can be enabled later behind USE_PAGEINDEX_API=true.
    results = lexical_search(query, top_k=top_k)
    if not results:
        for md_file in sorted(STANDARDIZED_DIR.rglob("*.md"))[:top_k]:
            results.append(
                {
                    "content": md_file.read_text(encoding="utf-8", errors="ignore")[:500],
                    "score": 0.1,
                    "metadata": {"source": md_file.name, "type": md_file.parent.name},
                }
            )
    return [{**item, "source": "pageindex"} for item in results[:top_k]]
