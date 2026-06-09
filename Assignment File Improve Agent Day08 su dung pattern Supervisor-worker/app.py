"""Chatbot RAG Streamlit cho demo nhóm."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.task10_generation import TOP_K, TOP_P, TEMPERATURE, generate_with_citation


def plain_text(text: str) -> str:
    """Bỏ markdown cơ bản để giao diện không bị chữ to/bôi đậm ngoài ý muốn."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        while stripped.startswith("#"):
            stripped = stripped[1:].lstrip()
        stripped = stripped.replace("**", "").replace("__", "").replace("`", "")
        lines.append(stripped)
    return " ".join(" ".join(lines).split())


def render_sources(sources: list[dict]):
    if not sources:
        st.info("Chưa có tài liệu nguồn.")
        return

    for index, source in enumerate(sources, 1):
        metadata = source.get("metadata", {})
        source_name = metadata.get("source", "không rõ")
        doc_type = metadata.get("type", "không rõ")
        score = source.get("score", 0)
        preview = plain_text(source.get("content", ""))[:550]

        with st.container(border=True):
            st.write(f"{index}. {source_name}")
            st.caption(f"Loại: {doc_type} | Điểm: {score:.3f}")
            st.text(preview)


st.set_page_config(
    page_title="Chatbot RAG pháp luật ma túy",
    page_icon="⚖️",
    layout="centered",
)

st.title("Chatbot RAG pháp luật ma túy")
st.write("Hỏi đáp về pháp luật ma túy Việt Nam và tin tức liên quan, có citation và tài liệu nguồn.")

with st.sidebar:
    st.header("Cấu hình")
    st.write(f"TOP_K: `{TOP_K}`")
    st.write(f"TOP_P: `{TOP_P}`")
    st.write(f"Temperature: `{TEMPERATURE}`")
    st.divider()
    st.write("Hybrid retrieval → rerank → generation")
    st.write("Thiếu evidence: `I cannot verify this information`")
    if st.button("Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

example = st.selectbox(
    "Câu hỏi mẫu",
    [
        "",
        "Pháp luật xử lý hành vi tàng trữ trái phép chất ma túy như thế nào?",
        "Nếu chỉ có tin đồn về nghệ sĩ và chất cấm thì có kết luận được không?",
        "Pipeline có cần citation khi trả lời về ma túy không?",
    ],
)

if example and st.button("Dùng câu hỏi mẫu"):
    st.session_state.example_prompt = example

if not st.session_state.messages:
    st.info("Nhập câu hỏi bên dưới hoặc chọn câu hỏi mẫu để bắt đầu.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(plain_text(message["content"]))
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander("Tài liệu nguồn"):
                render_sources(message["sources"])

prompt = st.chat_input("Nhập câu hỏi...")
if st.session_state.get("example_prompt"):
    prompt = st.session_state.pop("example_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    previous_user_turns = [
        message["content"]
        for message in st.session_state.messages
        if message["role"] == "user"
    ][-3:]
    enriched_query = " ".join(previous_user_turns)

    with st.spinner("Đang tìm tài liệu và tạo câu trả lời..."):
        result = generate_with_citation(enriched_query, top_k=TOP_K)

    answer = result["answer"]
    sources = result.get("sources", [])
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )

    with st.chat_message("assistant"):
        st.write(plain_text(answer))
        with st.expander("Tài liệu nguồn", expanded=True):
            render_sources(sources)
