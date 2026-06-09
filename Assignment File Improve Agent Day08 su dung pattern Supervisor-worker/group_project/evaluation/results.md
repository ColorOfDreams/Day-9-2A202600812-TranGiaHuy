# Kết quả đánh giá RAG

## Cách đánh giá

Bộ đánh giá offline dùng 4 chỉ số trong README: độ bám context, độ liên quan câu trả lời, độ bao phủ context và độ chính xác context.

## Bảng điểm tổng quan

| Chỉ số | Cấu hình A (hybrid + rerank) | Cấu hình B (hybrid không rerank) | Chênh lệch |
|--------|----------------------------|-----------------------------|-------|
| Độ bám context | 1.0 | 1.0 | +0.000 |
| Độ liên quan câu trả lời | 0.288 | 0.209 | +0.079 |
| Độ bao phủ context | 0.356 | 0.35 | +0.006 |
| Độ chính xác context | 0.421 | 0.425 | -0.004 |
| Trung bình | 0.516 | 0.496 | +0.020 |

## Phân tích A/B

Cấu hình A dùng hybrid retrieval, RRF merge và reranking. Cấu hình B vẫn dùng hybrid retrieval nhưng tắt reranking.
Cấu hình A được ưu tiên khi điểm trung bình bằng hoặc cao hơn vì kết quả cuối thường bám query tốt hơn.

## Các case yếu nhất

| # | Câu hỏi | Bám context | Liên quan | Bao phủ | Chính xác | Nguyên nhân |
|---|----------|--------------|-----------|--------|-----------|------------|
| 1 | Lexical search trong pipeline dùng cơ chế gì? | 1.0 | 0.062 | 0.077 | 0.143 | Corpus local còn thiếu chi tiết nguồn |
| 2 | Semantic search trả về định dạng kết quả nào? | 1.0 | 0.0 | 0.125 | 0.333 | Corpus local còn thiếu chi tiết nguồn |
| 3 | Generation tránh lost in the middle bằng cách nào? | 1.0 | 0.143 | 0.231 | 0.222 | Corpus local còn thiếu chi tiết nguồn |

## Đề xuất cải thiện

1. Thay summary fallback của tài liệu legal bằng markdown extract đầy đủ từ PDF để tăng recall.
2. Crawl URL báo thật thay vì JSON mẫu khi có internet.
3. Bật evaluator dùng LLM như DeepEval hoặc RAGAS khi demo/chấm thủ công.
