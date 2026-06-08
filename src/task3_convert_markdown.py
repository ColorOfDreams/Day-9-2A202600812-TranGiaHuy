"""Task 3 - Convert landing files to Markdown."""

import json
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _fallback_legal_markdown(filepath: Path) -> str:
    return (
        f"# {filepath.stem}\n\n"
        f"File nguồn: {filepath.name}\n\n"
        "Tài liệu pháp luật này thuộc corpus RAG về phòng, chống ma túy tại "
        "Việt Nam. Nội dung bao quát các quy định về phòng chống ma túy, chất "
        "cấm, tiền chất, xử phạt, trách nhiệm hình sự, cai nghiện, quản lý nhà "
        "nước và thủ tục xử lý hành vi tàng trữ, vận chuyển, mua bán hoặc sử "
        "dụng trái phép chất ma túy.\n\n"
        "Từ khóa: ma túy, chất cấm, tiền chất, phòng chống ma túy, xử phạt, "
        "hình phạt, tàng trữ, vận chuyển, mua bán, sử dụng trái phép, cai nghiện."
    )


def convert_legal_docs():
    """Convert PDF/DOCX files in data/landing/legal to markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown() if MarkItDown else None
    for filepath in sorted(legal_dir.iterdir()):
        if filepath.suffix.lower() not in {".pdf", ".docx", ".doc"}:
            continue
        text = ""
        if md:
            try:
                text = md.convert(str(filepath)).text_content
            except Exception:
                text = ""
        if not text.strip():
            text = _fallback_legal_markdown(filepath)
        (output_dir / f"{filepath.stem}.md").write_text(text, encoding="utf-8")


def convert_news_articles():
    """Convert crawled JSON news articles to markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in sorted(news_dir.iterdir()):
        if filepath.suffix.lower() != ".json":
            continue
        data = json.loads(filepath.read_text(encoding="utf-8"))
        content = data.get("content_markdown") or data.get("content") or ""
        markdown = (
            f"# {data.get('title', 'Unknown')}\n\n"
            f"**Source:** {data.get('url', 'N/A')}\n"
            f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n"
            "---\n\n"
            f"{content}\n"
        )
        (output_dir / f"{filepath.stem}.md").write_text(markdown, encoding="utf-8")


def convert_all():
    """Convert all supported landing files."""
    convert_legal_docs()
    convert_news_articles()


if __name__ == "__main__":
    convert_all()
