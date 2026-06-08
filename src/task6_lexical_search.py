"""Task 6 - BM25 lexical search with a pure-Python fallback."""

import math
import re
import unicodedata
from collections import Counter

from .task4_chunking_indexing import chunk_documents, load_documents

CORPUS: list[dict] = []


def _tokenize(text: str) -> list[str]:
    try:
        text = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        pass
    text = "".join(
        char for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )
    return re.findall(r"\w+", text, flags=re.UNICODE)


def _get_corpus() -> list[dict]:
    global CORPUS
    if not CORPUS:
        CORPUS = chunk_documents(load_documents())
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """Build a rank-bm25 index when installed; otherwise return tokens."""
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except ImportError:
        return tokenized_corpus


def _fallback_scores(tokenized_corpus: list[list[str]], query_tokens: list[str]) -> list[float]:
    doc_count = len(tokenized_corpus)
    avgdl = sum(len(doc) for doc in tokenized_corpus) / doc_count if doc_count else 0
    dfs = Counter(term for doc in tokenized_corpus for term in set(doc))
    scores = []
    for doc in tokenized_corpus:
        tf = Counter(doc)
        score = 0.0
        for term in query_tokens:
            if term not in tf:
                continue
            idf = math.log(1 + (doc_count - dfs[term] + 0.5) / (dfs[term] + 0.5))
            denom = tf[term] + 1.5 * (1 - 0.75 + 0.75 * len(doc) / (avgdl or 1))
            score += idf * (tf[term] * 2.5) / denom
        scores.append(score)
    return scores


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Return BM25-ranked chunks."""
    corpus = _get_corpus()
    if not corpus:
        return []
    query_tokens = _tokenize(query)
    index = build_bm25_index(corpus)
    scores = index.get_scores(query_tokens) if hasattr(index, "get_scores") else _fallback_scores(index, query_tokens)
    ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)
    return [
        {**corpus[index], "score": float(score)}
        for index, score in ranked[:top_k]
        if float(score) > 0
    ]


if __name__ == "__main__":
    for result in lexical_search("ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}")
