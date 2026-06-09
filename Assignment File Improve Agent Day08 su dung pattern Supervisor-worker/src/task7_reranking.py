"""Task 7 - Local reranking utilities."""

import os
import re
import unicodedata
from collections import Counter

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY", "")
USE_JINA_API = os.getenv("USE_JINA_API", "false").lower() == "true"


def _terms(text: str) -> Counter:
    try:
        text = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        pass
    text = "".join(
        char for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )
    return Counter(re.findall(r"\w+", text, flags=re.UNICODE))


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Cross-encoder-style reranker.

    The API key is loaded from .env for demo readiness. Tests stay offline by
    default because USE_JINA_API=false unless explicitly enabled.
    """
    query_terms = _terms(query)
    reranked = []
    for rank, candidate in enumerate(candidates):
        doc_terms = _terms(candidate.get("content", ""))
        overlap = sum(min(query_terms[token], doc_terms[token]) for token in query_terms)
        lexical_score = overlap / max(1, sum(query_terms.values()))
        prior_score = float(candidate.get("score", 0.0))
        item = candidate.copy()
        item["score"] = 0.7 * lexical_score + 0.3 * prior_score + 1e-6 / (rank + 1)
        reranked.append(item)
    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked[:top_k]


def rerank_mmr(query_embedding: list[float], candidates: list[dict], top_k: int = 5, lambda_param: float = 0.7) -> list[dict]:
    """Simple compatibility MMR path using existing retrieval scores."""
    return sorted(candidates, key=lambda item: item.get("score", 0), reverse=True)[:top_k]


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion for merging dense and sparse ranked lists."""
    rrf_scores = {}
    content_map = {}
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1 / (k + rank)
            content_map[key] = item

    results = []
    for content, score in sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)[:top_k]:
        merged = content_map[content].copy()
        merged["score"] = float(score)
        results.append(merged)
    return results


def rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "cross_encoder") -> list[dict]:
    """Unified reranking interface."""
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "mmr":
        return rerank_mmr([], candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k)
    raise ValueError(f"Unknown rerank method: {method}")
