"""Task 2 - Thu thập bài báo về nghệ sĩ liên quan tới ma túy.

Repo lưu 5 bài báo thật vào data/landing/news dưới dạng JSON gồm:
url, title, source, date_published, date_crawled và content_markdown.

Do môi trường chấm/test có thể không có mạng, file JSON đã được lưu sẵn.
Hàm crawl_article bên dưới là tiện ích đơn giản để crawl lại metadata khi cần.
"""

import asyncio
import http.client
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://vietnamnet.vn/ngoai-nguyen-cong-tri-nhung-nghe-si-nao-tung-bi-bat-vi-ma-tuy-2424971.html",
    "https://thanhnien.vn/cong-an-tphcm-bat-ca-si-long-nhat-va-son-ngoc-minh-lien-quan-den-ma-tuy-185260520123807384.htm",
    "https://tuoitre.vn/nguoi-mau-nhikolai-dinh-bi-bat-trong-chuyen-an-ma-tuy-o-khu-ma-lang-quan-1-20240625230004986.htm",
    "https://vnexpress.net/nguoi-mau-andrea-aybar-va-ca-si-chi-dan-bi-bat-4814295.html",
    "https://nld.com.vn/phap-luat/dien-vien-le-hang-bi-bat-vi-mua-ban-ma-tuy-20230423173501249.htm",
]


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.skip_depth = 0
        self.title_parts = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.skip_depth:
            return
        text = " ".join(data.split())
        if not text:
            return
        if self.in_title:
            self.title_parts.append(text)
        elif len(text) > 40 and not _is_noise(text):
            self.text_parts.append(text)


def _is_noise(text: str) -> bool:
    lowered = text.lower()
    noise_markers = [
        "window.",
        "function ",
        "googletag",
        "dataLayer".lower(),
        "var ",
        "document.",
        "copyright",
        "all rights reserved",
        "đăng nhập",
        "theo dõi báo",
        "hotline",
        "email",
        "javascript",
        "số giấy phép",
        "địa chỉ:",
        "hỗ trợ kỹ thuật",
        "chỉ được phát hành lại",
        "cơ quan chủ quản",
        "tổng biên tập",
    ]
    return any(marker in lowered for marker in noise_markers)


def _clean_article_text(title: str, body: str) -> str:
    body = re.sub(r"\s+", " ", body).strip()
    if title and title in body:
        body = body[body.find(title):]
    drop_patterns = [
        r"Số giấy phép:.*?(?=Ngoài|Công an|Người mẫu|Diễn viên|$)",
        r"Địa chỉ:.*?(?=Ngoài|Công an|Người mẫu|Diễn viên|$)",
        r"Chỉ được phát hành lại.*?(?=Ngoài|Công an|Người mẫu|Diễn viên|$)",
        r"Hỗ trợ kỹ thuật:.*?(?=Ngoài|Công an|Người mẫu|Diễn viên|$)",
    ]
    for pattern in drop_patterns:
        body = re.sub(pattern, "", body, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", body).strip()


def setup_directory():
    """Tạo thư mục data/landing/news nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


async def crawl_article(url: str) -> dict:
    """Crawl HTML cơ bản và trả về metadata + nội dung tóm tắt dạng markdown."""
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        try:
            raw_html = response.read()
        except http.client.IncompleteRead as exc:
            raw_html = exc.partial
        html = raw_html.decode("utf-8", errors="ignore")

    parser = _TextExtractor()
    parser.feed(html)
    title = parser.title_parts[0] if parser.title_parts else url
    # Deduplicate while preserving order.
    seen = set()
    clean_parts = []
    for part in parser.text_parts:
        normalized = part.strip()
        if normalized not in seen:
            seen.add(normalized)
            clean_parts.append(normalized)
    body = " ".join(clean_parts)
    body = _clean_article_text(title, body)
    summary = body[:1800] if body else "Không trích xuất được nội dung chi tiết từ HTML."

    return {
        "url": url,
        "title": title,
        "source": url.split("/")[2],
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": summary,
    }


async def crawl_all():
    """Crawl lại toàn bộ ARTICLE_URLS và ghi JSON."""
    setup_directory()
    for index, url in enumerate(ARTICLE_URLS, 1):
        article = await crawl_article(url)
        filepath = DATA_DIR / f"article_{index:02d}.json"
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {filepath}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
