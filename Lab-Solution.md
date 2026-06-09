# Tổng kết những việc đã làm cho DAY9

## 1. Mục tiêu tổng thể

Dự án DAY9 là một codelab về hệ thống multi-agent dùng:

- LangGraph
- LangChain
- OpenRouter
- A2A protocol
- FastAPI/Uvicorn
- Registry service
- Nhiều agent chuyên biệt: Customer, Law, Tax, Compliance

Trong quá trình làm, mục tiêu chính là:

1. Đọc hiểu dự án.
2. Hoàn thiện các bài tập codelab.
3. Chạy thử các stage.
4. Viết báo cáo giải thích từng phần.
5. Tạo UI Streamlit để quan sát luồng agent.
6. Tối ưu để có thể test flow cơ bản mà không phụ thuộc credit OpenRouter.
7. Push các thay đổi chính lên GitHub.

## 2. Đã đọc và giải thích cấu trúc dự án

Đã kiểm tra cấu trúc repo:

```text
common/
registry/
customer_agent/
law_agent/
tax_agent/
compliance_agent/
stages/
exercises/
docs/
report/
streamlit_app.py
test_client.py
```

Các thành phần chính:

- `registry/`: service discovery, chạy port `10000`.
- `customer_agent/`: entrypoint cho người dùng, chạy port `10100`.
- `law_agent/`: orchestrator pháp lý, chạy port `10101`.
- `tax_agent/`: agent chuyên thuế, chạy port `10102`.
- `compliance_agent/`: agent chuyên compliance, chạy port `10103`.
- `common/`: helper dùng chung như LLM factory, A2A client, Registry client.
- `stages/`: demo từng bước từ Stage 1 đến Stage 4.
- `exercises/`: bài tập cần hoàn thiện.
- `test_client.py`: client test end-to-end Stage 5.

## 3. Đã giải thích 4 file tài liệu chính

Đã tóm tắt vai trò của:

```text
README.md
CODELAB.md
INSTRUCTOR_GUIDE.md
QUICK_REFERENCE.md
```

Tóm gọn:

- `README.md`: giới thiệu dự án, kiến trúc, cách setup/chạy.
- `CODELAB.md`: tài liệu học chính cho sinh viên.
- `INSTRUCTOR_GUIDE.md`: hướng dẫn dạy/chấm cho giảng viên.
- `QUICK_REFERENCE.md`: cheatsheet lệnh, keyword, lỗi thường gặp.

## 4. Đã cài và cấu hình `uv`

Ban đầu máy chưa nhận lệnh:

```text
uv : The term 'uv' is not recognized
```

Đã cài `uv` bằng installer chính thức.

Sau đó chạy:

```powershell
uv sync
```

Kết quả:

- Tạo được `.venv`.
- Cài dependencies từ `pyproject.toml` và `uv.lock`.
- Sau này thêm `streamlit` cũng đã sync thành công.

## 5. Đã tạo và cấu hình `.env`

Đã tạo `.env` từ `.env.example`.

Ban đầu model là:

```env
OPENROUTER_MODEL=anthropic/claude-sonnet-4-5
```

Vấn đề:

- Claude Sonnet chất lượng tốt nhưng tốn credit rất nhanh.
- Khi chạy nhiều stage và multi-agent, OpenRouter báo lỗi `402` do thiếu credit.

Đã thử nhiều model:

- `google/gemini-3.1-flash-lite`
- `openrouter/owl-alpha`
- `nex-agi/nex-n2-pro:free`
- `nvidia/nemotron-3-ultra-550b-a55b:free`
- `qwen/qwen3.7-plus`
- `inclusionai/ring-2.6-1t`

Model dùng tốt nhất cho Stage 2 và Stage 3 trong điều kiện hiện tại:

```env
OPENROUTER_MODEL=nex-agi/nex-n2-pro:free
```

## 6. Đã tối ưu `common/llm.py`

File:

```text
common/llm.py
```

Đã thêm:

```python
temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.3")),
max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "100")),
```

Mục đích:

- `temperature=0.3`: output ổn định hơn.
- `max_tokens`: tránh request quá nhiều output token, giảm lỗi thiếu credit.

## 7. Đã hoàn thiện Exercise 2

File:

```text
exercises/exercise_2_tools.py
```

Đã làm:

- Thêm knowledge base entry về luật lao động Việt Nam.
- Thêm tool `check_statute_of_limitations`.
- Thêm tool vào danh sách tools.
- Dùng `tool_map` để xử lý tool call gọn hơn.
- Xóa TODO/pass trong bài tập.

Tool mới:

```python
check_statute_of_limitations(case_type: str)
```

Tool này xử lý các case:

- contract/breach/hop dong
- labor/employment/lao dong/sa thai
- tort/injury/negligence/boi thuong

Kết quả test:

- Tool chạy trực tiếp OK.
- Exercise 2 chạy được khi OpenRouter còn credit.

## 8. Đã hoàn thiện Exercise 4

File:

```text
exercises/exercise_4_multiagent.py
```

Đã làm:

- Thêm `privacy_analysis`.
- Thêm flags:
  - `needs_tax`
  - `needs_compliance`
  - `needs_privacy`
- Thêm `privacy_agent`.
- Thêm routing cho privacy/data/GDPR/data breach.
- Thêm node `privacy_agent` vào graph.
- Thêm edge từ `privacy_agent` sang `aggregate_results`.
- Thêm privacy section vào aggregator.

Đã chỉnh routing đúng kiểu LangGraph:

- `check_routing` chỉ trả flags.
- `route_to_specialists` mới dispatch bằng `Send`.

Kết quả test:

- `build_graph()` OK.
- Routing với câu hỏi có `data breach` và `tax` chọn đúng:
  - `tax_agent`
  - `privacy_agent`

## 9. Đã chạy và báo cáo Stage 1

File stage:

```text
stages/stage_1_direct_llm/main.py
```

Đã đổi câu hỏi:

```python
QUESTION = "Wrongful termination remedies?"
```

Đã rút gọn system prompt để phù hợp credit:

```python
"You are a legal expert. Answer briefly."
```

Stage 1 chạy thành công với model `openrouter/owl-alpha`.

Output mẫu:

```text
Wrongful termination remedies typically include reinstatement, back pay,
compensatory damages, and sometimes punitive damages.
```

Báo cáo:

```text
report/phan_1_direct_llm_report.md
```

## 10. Đã chạy và báo cáo Stage 2

File stage:

```text
stages/stage_2_rag_tools/main.py
```

Đã chạy thành công với:

```text
nex-agi/nex-n2-pro:free
```

Stage 2 đã chứng minh:

- LLM nhận tools.
- LLM tự gọi `search_legal_database`.
- Python chạy tool thật.
- Kết quả tool được đưa lại qua `ToolMessage`.
- LLM sinh final answer dựa trên tool result.

Output quan trọng:

```text
Tool: search_legal_database
Args: {'query': 'legal consequences breach of non-disclosure agreement damages injunction trade secrets'}
```

Đã chỉnh nhẹ:

```python
ToolMessage(content=result[:900], tool_call_id=tc["id"])
```

Mục đích:

- Tránh prompt quá dài khi credit thấp.
- Giữ đúng luồng codelab.

Báo cáo:

```text
report/phan_2_stage_2_rag_tools_report.md
```

## 11. Đã chạy và báo cáo Stage 3

File stage:

```text
stages/stage_3_single_agent/main.py
```

Stage 3 chạy thành công với model:

```text
nex-agi/nex-n2-pro:free
```

Điểm quan trọng nhất:

Agent gọi tool sai:

```text
Tool: calculate_penalty
Args: {}
```

Tool báo lỗi thiếu tham số:

```text
violation_type: Field required
severity: Field required
annual_revenue: Field required
```

Sau đó agent tự sửa và gọi lại đúng:

```text
Tool: calculate_penalty
Args: {'annual_revenue': 5000000, 'severity': 'high', 'violation_type': 'data_privacy'}

Tool: calculate_penalty
Args: {'annual_revenue': 5000000, 'severity': 'high', 'violation_type': 'tax_evasion'}
```

Điều này chứng minh ReAct loop:

```text
Think -> Act -> Observe -> sửa lỗi -> Act lại -> Final Answer
```

Báo cáo:

```text
report/phan_3_stage_3_react_agent_report.md
```

## 12. Đã chạy và báo cáo Stage 4

File stage:

```text
stages/stage_4_milti_agent/main.py
```

Lưu ý:

Tên thư mục đang là `stage_4_milti_agent`, sai chính tả so với `multi`.

Đã thử nhiều model:

- `nex-agi/nex-n2-pro:free`: lỗi `504`.
- `nvidia/nemotron-3-ultra-550b-a55b:free`: lỗi `504`.
- `qwen/qwen3.7-plus`: lỗi credit/rate limit.
- `inclusionai/ring-2.6-1t`: graph chạy hết nhưng LLM trả rỗng.

Output quan trọng:

```text
[Node: check_routing] needs_tax=True, needs_compliance=True
[Node: call_tax_specialist] Tax specialist agent starting...
[Node: call_compliance_specialist] Compliance specialist agent starting...
[Node: aggregate] Combining all specialist analyses...
```

Kết luận:

- Graph topology chạy đúng.
- Routing đúng.
- Tax và Compliance branch được dispatch song song.
- Final answer chưa có nội dung tốt do provider/model/credit.

Báo cáo:

```text
report/phan_4_stage_4_multi_agent_report.md
```

## 13. Đã tạo folder report

Folder:

```text
report/
```

Đã tạo các file:

```text
report/phan_1_direct_llm_report.md
report/phan_2_stage_2_rag_tools_report.md
report/phan_3_stage_3_react_agent_report.md
report/phan_4_stage_4_multi_agent_report.md
```

Folder `report/` đã được thêm vào `.gitignore`, nên không bị push lên GitHub.

## 14. Đã tạo UI Streamlit

File:

```text
streamlit_app.py
```

Đã thêm dependency:

```toml
streamlit>=1.41.0
```

Đã chạy:

```powershell
uv sync
```

UI có:

- Sidebar chọn Stage 1-5.
- Sơ đồ luồng agent bằng Graphviz.
- Tab chạy demo stage.
- Tab keyword và phần cần chú ý.
- Tab đọc report Markdown.
- Thông tin port Stage 5.
- Override model và `OPENROUTER_MAX_TOKENS`.

Lệnh chạy UI:

```powershell
uv run streamlit run streamlit_app.py
```

Hoặc:

```powershell
C:\Users\Dell\.local\bin\uv.exe run streamlit run streamlit_app.py
```

## 15. Đã push một commit lên GitHub

Đã commit và push:

```text
e3d2cb2 Add Streamlit lab UI and complete exercises
```

Remote:

```text
https://github.com/ColorOfDreams/Day-9-2A202600812-TranGiaHuy.git
```

Commit này gồm:

- Exercise 2.
- Exercise 4.
- Streamlit UI.
- Dependency `streamlit`.
- Cấu hình LLM tiết kiệm token.
- `.gitignore` cho report/log.

## 16. Đã tối ưu thêm luồng Stage 5 bằng mock mode

Sau khi bạn đưa sơ đồ luồng:

```text
User
  -> Customer Agent :10100
  -> Registry :10000 discover legal
  -> Law Agent :10101
  -> Registry discover tax/compliance
  -> Tax Agent :10102
  -> Compliance Agent :10103
  -> Response
```

Đã thêm chế độ:

```env
MOCK_AGENT_RESPONSES=1
```

Mục đích:

- Test được full Registry/A2A flow.
- Không gọi LLM.
- Không phụ thuộc OpenRouter credit.
- Không phụ thuộc provider free bị timeout.

Đã chỉnh các file:

```text
customer_agent/agent_executor.py
law_agent/agent_executor.py
tax_agent/agent_executor.py
compliance_agent/agent_executor.py
.env.example
.gitignore
```

## 17. Mock flow test đã PASS

Đã bật 5 service local với:

```env
MOCK_AGENT_RESPONSES=1
```

Sau đó chạy:

```powershell
uv run python test_client.py
```

Output chính:

```text
RESPONSE:
============================================================
Mock legal analysis

Question: If a company breaks a contract and avoids taxes, what are the legal and regulatory consequences?

Legal: contract breach can trigger damages, injunctions, and business liability.

Tax: Mock tax analysis: tax avoidance/evasion may create back-tax, interest, civil penalties, and possible criminal exposure.

Compliance: Mock compliance analysis: regulatory exposure may include SEC/FTC review, governance remediation, controls testing, and reporting duties.
============================================================
```

Logs xác nhận flow:

```text
Customer -> Registry discover legal_question
Customer -> Law Agent via A2A
Law -> Registry discover tax_question
Law -> Registry discover compliance_question
Law -> Tax Agent via A2A
Law -> Compliance Agent via A2A
Customer receives response
```

## 18. Trạng thái hiện tại

Các thay đổi mock mode hiện tại chưa commit/push.

Files đang thay đổi:

```text
.env.example
.gitignore
customer_agent/agent_executor.py
law_agent/agent_executor.py
tax_agent/agent_executor.py
compliance_agent/agent_executor.py
```

## 19. Cách chạy ổn định nhất hiện tại

Để test flow cơ bản:

```env
MOCK_AGENT_RESPONSES=1
```

Chạy 5 terminal:

```powershell
uv run python -m registry
uv run python -m tax_agent
uv run python -m compliance_agent
uv run python -m law_agent
uv run python -m customer_agent
```

Terminal khác:

```powershell
uv run python test_client.py
```

Nếu muốn chạy LLM thật:

```env
MOCK_AGENT_RESPONSES=0
OPENROUTER_MODEL=nex-agi/nex-n2-pro:free
OPENROUTER_MAX_TOKENS=120
```

Nhưng LLM thật vẫn phụ thuộc provider và credit.

## 20. Kết luận

DAY9 hiện đã có:

- Code bài tập hoàn thiện.
- Báo cáo từng stage.
- UI Streamlit.
- Test mock flow ổn định.
- Cấu hình model rẻ/free hơn.
- Cách chạy không phụ thuộc OpenRouter bằng `MOCK_AGENT_RESPONSES=1`.

Phần nên làm tiếp nếu muốn hoàn thiện hơn:

1. Commit/push mock mode mới.
2. Sửa typo folder `stage_4_milti_agent` nếu không sợ ảnh hưởng tài liệu.
3. Thêm script PowerShell để start 5 service trên Windows.
4. Thêm test tự động cho Registry discovery và mock A2A flow.
