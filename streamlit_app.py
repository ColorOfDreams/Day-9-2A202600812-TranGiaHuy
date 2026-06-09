"""Streamlit UI for exploring the legal multi-agent codelab."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Stage:
    label: str
    title: str
    script: str | None
    summary: str
    flow_dot: str
    keywords: list[str]
    notes: list[str]


STAGES = {
    "stage1": Stage(
        label="Stage 1",
        title="Direct LLM Calling",
        script="stages/stage_1_direct_llm/main.py",
        summary="Gọi LLM trực tiếp bằng SystemMessage và HumanMessage. Chưa có tool, chưa có RAG, chưa có memory.",
        flow_dot="""
digraph {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#F8FAFC", color="#94A3B8", fontname="Arial"];
  user [label="User question"];
  messages [label="SystemMessage + HumanMessage"];
  llm [label="LLM via OpenRouter"];
  answer [label="Text response"];
  user -> messages -> llm -> answer;
}
""",
        keywords=["get_llm", "ChatOpenAI", "SystemMessage", "HumanMessage", "ainvoke", "temperature", "max_tokens"],
        notes=[
            "Đây là luồng đơn giản nhất: prompt vào, text ra.",
            "Không có nguồn dữ liệu ngoài nên câu trả lời chưa được grounded.",
            "Nếu output ngắn, kiểm tra OPENROUTER_MAX_TOKENS.",
        ],
    ),
    "stage2": Stage(
        label="Stage 2",
        title="LLM + RAG & Tools",
        script="stages/stage_2_rag_tools/main.py",
        summary="LLM được bind tools, tự yêu cầu gọi tool, Python chạy tool rồi đưa kết quả lại qua ToolMessage.",
        flow_dot="""
digraph {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#F8FAFC", color="#94A3B8", fontname="Arial"];
  user [label="User question"];
  llm1 [label="LLM + bind_tools"];
  calls [label="tool_calls"];
  tool [label="Python tool execution"];
  msg [label="ToolMessage"];
  llm2 [label="LLM final synthesis"];
  answer [label="Grounded answer"];
  user -> llm1 -> calls -> tool -> msg -> llm2 -> answer;
}
""",
        keywords=["RAG", "@tool", "bind_tools", "tool_calls", "ToolMessage", "LEGAL_KNOWLEDGE", "query"],
        notes=[
            "LLM không tự chạy Python; nó chỉ yêu cầu gọi tool.",
            "Tool docstring rất quan trọng vì model dựa vào đó để hiểu cách dùng tool.",
            "Knowledge base hiện chỉ match keyword, chưa phải vector search.",
        ],
    ),
    "stage3": Stage(
        label="Stage 3",
        title="Single Agent ReAct Loop",
        script="stages/stage_3_single_agent/main.py",
        summary="Một agent tự lặp Think, Act, Observe cho đến khi đủ thông tin để trả lời.",
        flow_dot="""
digraph {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#F8FAFC", color="#94A3B8", fontname="Arial"];
  user [label="Complex question"];
  agent [label="ReAct agent"];
  think [label="Think"];
  act [label="Act: call tool"];
  observe [label="Observe result/error"];
  final [label="Final answer"];
  user -> agent -> think -> act -> observe -> think;
  observe -> final;
}
""",
        keywords=["ReAct", "create_react_agent", "Think", "Act", "Observe", "astream", "tools node"],
        notes=[
            "Agent có thể gọi tool sai rồi tự sửa sau khi quan sát lỗi.",
            "Vẫn chỉ là một agent, nên chưa có chuyên môn hóa theo từng domain.",
            "Phù hợp để xử lý câu hỏi nhiều bước nhưng chưa cần multi-agent.",
        ],
    ),
    "stage4": Stage(
        label="Stage 4",
        title="Multi-Agent In-Process",
        script="stages/stage_4_milti_agent/main.py",
        summary="Lead legal node phân tích, router quyết định specialist, Tax và Compliance chạy song song bằng Send.",
        flow_dot="""
digraph {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#F8FAFC", color="#94A3B8", fontname="Arial"];
  user [label="Question"];
  law [label="analyze_law"];
  route [label="check_routing"];
  tax [label="call_tax_specialist"];
  comp [label="call_compliance_specialist"];
  agg [label="aggregate"];
  final [label="Final answer"];
  user -> law -> route;
  route -> tax;
  route -> comp;
  tax -> agg;
  comp -> agg;
  agg -> final;
}
""",
        keywords=["StateGraph", "Send", "conditional_edges", "Reducer", "Parallel branches", "aggregate"],
        notes=[
            "Stage 4 chạy trong một process, chưa có HTTP/A2A.",
            "Send là điểm quan trọng để dispatch nhiều branch song song.",
            "Reducer giúp merge state khi các branch song song cùng ghi dữ liệu.",
        ],
    ),
    "stage5": Stage(
        label="Stage 5",
        title="Distributed A2A System",
        script=None,
        summary="Các agent tách thành service riêng, tự register vào Registry và giao tiếp bằng A2A protocol.",
        flow_dot="""
digraph {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#F8FAFC", color="#94A3B8", fontname="Arial"];
  user [label="User"];
  customer [label="Customer Agent :10100"];
  registry [label="Registry :10000"];
  law [label="Law Agent :10101"];
  tax [label="Tax Agent :10102"];
  comp [label="Compliance Agent :10103"];
  answer [label="Response"];
  user -> customer;
  customer -> registry [label="discover legal"];
  customer -> law [label="A2A"];
  law -> registry [label="discover tax/compliance"];
  law -> tax [label="A2A"];
  law -> comp [label="A2A"];
  tax -> law;
  comp -> law;
  law -> customer -> answer;
}
""",
        keywords=["A2A", "Registry", "AgentCard", "Task", "trace_id", "context_id", "delegate"],
        notes=[
            "Stage 5 cần chạy nhiều service cùng lúc.",
            "Registry giúp discovery động, tránh hardcode endpoint.",
            "test_client.py dùng để test end-to-end, không phải grader tự động.",
        ],
    ),
}


def run_stage(script: str, max_tokens: int, model_override: str | None) -> tuple[int, str]:
    env = os.environ.copy()
    env["OPENROUTER_MAX_TOKENS"] = str(max_tokens)
    if model_override:
        env["OPENROUTER_MODEL"] = model_override

    proc = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=360,
    )
    output = "\n".join(part for part in [proc.stdout, proc.stderr] if part)
    return proc.returncode, output


def render_metric_row() -> None:
    cols = st.columns(5)
    items = [
        ("Registry", "10000"),
        ("Customer", "10100"),
        ("Law", "10101"),
        ("Tax", "10102"),
        ("Compliance", "10103"),
    ]
    for col, (name, port) in zip(cols, items):
        col.metric(name, port)


st.set_page_config(
    page_title="Legal Multi-Agent Lab",
    page_icon=None,
    layout="wide",
)

st.markdown(
    """
<style>
  .block-container { padding-top: 1.5rem; }
  [data-testid="stMetricValue"] { font-size: 1.2rem; }
  .small-note { color: #475569; font-size: 0.92rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Legal Multi-Agent Lab")
st.caption("Dashboard Streamlit để quan sát luồng LLM, tools, ReAct, multi-agent và A2A.")

with st.sidebar:
    st.header("Điều khiển")
    stage_key = st.radio(
        "Chọn stage",
        list(STAGES.keys()),
        format_func=lambda key: f"{STAGES[key].label} - {STAGES[key].title}",
    )
    selected = STAGES[stage_key]

    st.divider()
    st.subheader("Cấu hình chạy")
    current_model = os.getenv("OPENROUTER_MODEL", "")
    st.text_input("Model trong .env", current_model, disabled=True)
    model_override = st.text_input("Override model cho lần chạy", "")
    max_tokens = st.slider("OPENROUTER_MAX_TOKENS", 30, 500, 120, step=10)

    st.divider()
    st.subheader("Lệnh nhanh")
    if selected.script:
        st.code(f"uv run python {selected.script}", language="powershell")
    else:
        st.code("uv run python test_client.py", language="powershell")

top_left, top_right = st.columns([1.5, 1])
with top_left:
    st.subheader(f"{selected.label}: {selected.title}")
    st.write(selected.summary)
with top_right:
    st.subheader("Stage 5 ports")
    render_metric_row()

tab_flow, tab_run, tab_notes, tab_reports = st.tabs(
    ["Luồng agent", "Chạy demo", "Keyword và chú ý", "Report"]
)

with tab_flow:
    st.graphviz_chart(selected.flow_dot, width="stretch")
    if stage_key == "stage4":
        st.info("Stage 4 dùng LangGraph Send để chạy Tax và Compliance branches song song trong cùng một process.")
    if stage_key == "stage5":
        st.warning("Stage 5 cần bật Registry và 4 agent service trước khi chạy test_client.py.")

with tab_run:
    if selected.script is None:
        st.write("Stage 5 là distributed system, nên UI này không tự bật 5 service để tránh chiếm port.")
        st.code(
            """
uv run python -m registry
uv run python -m tax_agent
uv run python -m compliance_agent
uv run python -m law_agent
uv run python -m customer_agent
uv run python test_client.py
""".strip(),
            language="powershell",
        )
    else:
        st.write("Chạy script stage được chọn bằng Python hiện tại của môi trường Streamlit.")
        if st.button("Chạy stage", type="primary"):
            with st.spinner("Đang chạy, có thể mất vài phút nếu model free chậm..."):
                try:
                    code, output = run_stage(
                        selected.script,
                        max_tokens=max_tokens,
                        model_override=model_override.strip() or None,
                    )
                except subprocess.TimeoutExpired as exc:
                    code = -1
                    output = f"Timeout sau {exc.timeout} giây. Model/provider có thể đang chậm."
                except Exception as exc:  # noqa: BLE001 - show UI-friendly error
                    code = -1
                    output = f"Lỗi khi chạy stage: {exc}"

            if code == 0:
                st.success("Stage chạy xong.")
            else:
                st.error(f"Stage kết thúc với exit code {code}.")
            st.text_area("Output", output, height=520)

with tab_notes:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Keyword")
        for keyword in selected.keywords:
            st.markdown(f"- `{keyword}`")
    with col_b:
        st.subheader("Cần chú ý")
        for note in selected.notes:
            st.markdown(f"- {note}")

with tab_reports:
    report_map = {
        "stage1": ROOT / "report" / "phan_1_direct_llm_report.md",
        "stage2": ROOT / "report" / "phan_2_stage_2_rag_tools_report.md",
        "stage3": ROOT / "report" / "phan_3_stage_3_react_agent_report.md",
        "stage4": ROOT / "report" / "phan_4_stage_4_multi_agent_report.md",
    }
    report_path = report_map.get(stage_key)
    if report_path and report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    elif stage_key == "stage5":
        st.write("Chưa có report riêng cho Stage 5 trong folder report.")
    else:
        st.write("Chưa có report cho stage này.")
