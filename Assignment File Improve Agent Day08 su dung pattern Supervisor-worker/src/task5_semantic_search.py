"""Task 5 - Offline semantic-style search."""

import math
import re
import unicodedata
from collections import Counter

from .task4_chunking_indexing import chunk_documents, load_documents


def hyde_expand_query(query: str) -> str:
    """Mở rộng query theo hướng HyDE đơn giản để tăng recall khi demo bonus.

    HyDE đầy đủ sẽ dùng LLM sinh hypothetical document. Bản offline này tạo
    một đoạn giả định ngắn, đủ để retrieval có thêm ngữ cảnh mà không cần API.
    """
    hypothetical_answer = (
        "Câu trả lời giả định có thể liên quan đến pháp luật ma túy Việt Nam, "
        "chất cấm, xử phạt, hình phạt, cai nghiện, nghệ sĩ, báo chí và nguồn trích dẫn."
    )
    return f"{query} {hypothetical_answer}"


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


def _cosine(a: Counter, b: Counter) -> float:
    numerator = sum(a[token] * b[token] for token in set(a) & set(b))
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    return numerator / (norm_a * norm_b) if norm_a and norm_b else 0.0


def semantic_search(query: str, top_k: int = 10, use_hyde: bool = False) -> list[dict]:
    """Return chunks sorted by cosine similarity over local token vectors."""
    retrieval_query = hyde_expand_query(query) if use_hyde else query
    query_vec = Counter(_tokenize(retrieval_query))
    results = []
    for chunk in chunk_documents(load_documents()):
        score = _cosine(query_vec, Counter(_tokenize(chunk["content"])))
        if score > 0:
            results.append({**chunk, "score": float(score)})
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("hinh phat ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}")
