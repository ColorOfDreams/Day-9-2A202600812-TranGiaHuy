# Bài tập nhóm - Chatbot RAG và đánh giá

## Mục tiêu

Xây dựng demo RAG chạy local cho tài liệu pháp luật Việt Nam về ma túy và các bài tin tức liên quan. Nhóm làm cả hai phần để lấy điểm nhóm ổn định:

- Chatbot RAG có trích dẫn, memory hội thoại và hiển thị tài liệu nguồn.
- Pipeline đánh giá có golden dataset, 4 chỉ số, so sánh A/B và báo cáo kết quả.

## Kiến trúc hệ thống

```text
PDF/JSON trong data/landing
        |
        v
Task 3 - Convert Markdown
        |
        v
data/standardized/*.md
        |
        v
Task 4 - Chunking
        |
        +--> Task 5 - Semantic search
        |
        +--> Task 6 - Lexical search / BM25 fallback
                  |
                  v
Task 9 - Hybrid retrieval + RRF merge
        |
        v
Task 7 - Reranking
        |
        +--> Task 8 - PageIndex/vectorless fallback
        |
        v
Task 10 - Generation có citation
        |
        v
app.py - Streamlit chatbot
```

## Phân công nhóm

| Người | Họ tên | MSSV | Vai trò | Trạng thái |
|-------|--------|------|---------|------------|
| P1 | Thành viên nhóm | | Integration Lead | Chờ nhóm ghép |
| P2 | Thành viên nhóm | | Chatbot / Frontend | Chờ nhóm ghép |
| P3 | Thành viên nhóm | | Conversation + Deploy | Chờ nhóm ghép |
| P4 | Thành viên nhóm | | Eval: Dataset + Metrics | Chờ nhóm ghép |
| P5 | Thành viên nhóm | | Eval: A/B + Báo cáo | Chờ nhóm ghép |
| P6 | Tran Gia Huy | 2A202600812 | Kiến trúc + README + Bonus | Hoàn thành |

## Phần P6 đã làm

- Vẽ và mô tả kiến trúc hệ thống trong README này.
- Điền bảng phân công nhóm.
- Chuẩn bị giải thích lexical search/BM25 cho demo.
- Chuẩn bị hướng HyDE đơn giản để mở rộng retrieval khi cần.
- Dọn repo để push: `.gitignore`, `.gitattributes`, không commit `.env`, cache hoặc `.venv`.

## Chatbot

Chatbot nằm ở `app.py`.

Tính năng:

- Giao diện chat bằng Streamlit.
- Gọi `generate_with_citation` từ Task 10.
- Có memory ngắn bằng cách ghép các lượt hỏi gần nhất.
- Hiển thị tài liệu nguồn, loại tài liệu và điểm retrieval.
- Khi không đủ bằng chứng trong context, hệ thống trả về đúng câu: `I cannot verify this information`.

Chạy app:

```bash
streamlit run app.py
```

Hoặc:

```bash
python -m streamlit run app.py
```

## Evaluation

Các file:

- `group_project/evaluation/golden_dataset.json`: 15 cặp Q&A.
- `group_project/evaluation/eval_pipeline.py`: script đánh giá offline.
- `group_project/evaluation/results.md`: báo cáo kết quả.

Các chỉ số:

- Độ bám context.
- Độ liên quan câu trả lời.
- Độ bao phủ context.
- Độ chính xác context.

Cấu hình A/B:

- Cấu hình A: hybrid retrieval + reranking.
- Cấu hình B: hybrid retrieval không reranking.

Chạy evaluation:

```bash
python group_project/evaluation/eval_pipeline.py
```

## Giải thích lexical search cho demo

Lexical search tìm theo từ khóa xuất hiện trong document. Pipeline ưu tiên BM25 nếu có thư viện `rank-bm25`.

BM25 hoạt động theo ba ý chính:

- Từ khóa xuất hiện nhiều trong chunk thì điểm cao hơn.
- Từ khóa hiếm trong toàn corpus thì quan trọng hơn.
- Document quá dài không được ưu tiên quá mức nhờ length normalization.

Trong repo này có fallback BM25 thuần Python để demo/test vẫn chạy nếu chưa cài đủ dependency.

## HyDE đề xuất cho bonus

HyDE là cách sinh một câu trả lời giả định từ query, sau đó dùng câu giả định đó để retrieval. Ý tưởng là query ngắn hoặc mơ hồ sẽ được mở rộng thành đoạn giàu ngữ cảnh hơn, giúp semantic retrieval tăng recall.

Luồng HyDE đề xuất:

```text
Query gốc
  -> Sinh hypothetical answer ngắn
  -> Ghép query gốc + hypothetical answer
  -> Semantic search / hybrid search
  -> Rerank
  -> Generation có citation
```

Trong bản nộp này, pipeline vẫn chạy offline để ổn định điểm. Nếu demo bonus, có thể bật LLM trong `.env` và dùng HyDE trước Task 5.

## Trạng thái bài cá nhân

Test cá nhân đã pass:

```bash
python -m pytest tests/test_individual.py -q
```

Kết quả:

```text
35 passed
```

## Ghi chú

Repo dùng fallback local/offline để test và demo có thể chạy không cần gọi API trả phí. API key vẫn được load từ `.env`, nhưng các call bên ngoài bị tắt mặc định nếu chưa bật flag `USE_*_API=true`.
