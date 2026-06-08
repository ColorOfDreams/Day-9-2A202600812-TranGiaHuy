"""Task 10 - Generation có citation."""

import os
import re
import unicodedata

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from .task9_retrieval_pipeline import retrieve

if load_dotenv:
    load_dotenv()

# TOP_K=5 để có đủ evidence nhưng context không quá dài.
TOP_K = 5
# TOP_P=0.9 cân bằng giữa độ linh hoạt và độ ổn định khi demo gọi API.
TOP_P = 0.9
# Temperature thấp để câu trả lời RAG bám dữ kiện hơn.
TEMPERATURE = 0.3
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_OPENAI_API = os.getenv("USE_OPENAI_API", "false").lower() == "true"

SYSTEM_PROMPT = """Trả lời bằng tiếng Việt và chỉ dùng context được cung cấp.
Mỗi khẳng định mang tính sự thật phải có citation. Nếu thiếu evidence, trả lời:
I cannot verify this information."""

STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from",
    "khong", "trong", "ngoai", "corpus", "thong", "tin", "nay",
    "cho", "cua", "voi", "cac", "nhung", "mot", "duoc", "the",
}


def _evidence_terms(text: str) -> set[str]:
    try:
        text = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        pass
    text = "".join(
        char for char in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(char) != "Mn"
    )
    return {
        token for token in re.findall(r"\w+", text, flags=re.UNICODE)
        if len(token) > 2 and token not in STOPWORDS
    }


def _plain_text(text: str) -> str:
    """Chuyển markdown đơn giản thành text thường để UI không bị chữ to/bôi đậm."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        stripped = re.sub(r"^#{1,6}\s*", "", stripped)
        stripped = stripped.replace("**", "").replace("__", "")
        stripped = stripped.replace("`", "")
        lines.append(stripped)
    return " ".join(" ".join(lines).split())


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đặt chunk mạnh nhất ở đầu và chunk mạnh tiếp theo gần cuối."""
    if len(chunks) <= 2:
        return chunks
    reordered = [chunks[index] for index in range(0, len(chunks), 2)]
    reordered.extend(chunks[index] for index in range(len(chunks) - 1 - (len(chunks) % 2 == 0), 0, -2))
    return reordered


def format_context(chunks: list[dict]) -> str:
    """Format chunks kèm nhãn nguồn để dùng citation."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Nguồn {index}")
        doc_type = metadata.get("type", "không rõ")
        parts.append(f"[Tài liệu {index} | Nguồn: {source} | Loại: {doc_type}]\n{chunk.get('content', '')}")
    return "\n---\n".join(parts)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Retrieve context và sinh câu trả lời có citation.

    OPENAI_API_KEY được load từ .env để sẵn sàng demo. Mặc định hàm dùng
    generation local deterministic để pytest không phụ thuộc API, mạng hay quota.
    """
    chunks = retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    if not reordered:
        return {"answer": "I cannot verify this information", "sources": [], "retrieval_source": "none"}

    best_score = max(float(chunk.get("score", 0.0)) for chunk in reordered)
    query_terms = _evidence_terms(query)
    context_terms = _evidence_terms(" ".join(chunk.get("content", "") for chunk in reordered))
    overlap_count = len(query_terms & context_terms)
    if query_terms and overlap_count == 0:
        return {
            "answer": "I cannot verify this information",
            "sources": chunks,
            "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
        }

    snippets = []
    for chunk in reordered[:3]:
        source = chunk.get("metadata", {}).get("source", "nguồn-không-rõ")
        snippet = _plain_text(chunk.get("content", ""))[:260]
        if snippet:
            snippets.append(f"{snippet} [{source}]")

    return {
        "answer": " ".join(snippets) if snippets else "I cannot verify this information",
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
    }
