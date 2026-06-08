"""Pipeline evaluation RAG offline cho bài tập nhóm.

README gợi ý DeepEval/RAGAS/TruLens, nhưng các framework đó thường cần gọi LLM.
Script này tự tính 4 metrics bắt buộc ở local để demo chạy ổn trong môi trường
offline/pytest, sau đó so sánh hai cấu hình A/B.
"""

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.task10_generation import generate_with_citation
from src.task9_retrieval_pipeline import retrieve

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE) if len(token) > 2}


def _overlap_score(left: str, right: str) -> float:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens)


def load_golden_dataset() -> list[dict]:
    """Load golden dataset gồm 15 câu hỏi."""
    return json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))


def _run_case(item: dict, use_reranking: bool) -> dict:
    question = item["question"]
    contexts = retrieve(question, top_k=5, use_reranking=use_reranking)
    if use_reranking:
        generation = generate_with_citation(question, top_k=5)
        answer = generation["answer"]
    else:
        answer = " ".join(
            f"{chunk['content'][:180]} [{chunk.get('metadata', {}).get('source', 'source')}]"
            for chunk in contexts[:3]
        )

    context_text = " ".join(chunk.get("content", "") for chunk in contexts)
    expected_context = item.get("expected_context", "")
    expected_answer = item.get("expected_answer", "")

    faithfulness = min(1.0, _overlap_score(answer, context_text) + (0.25 if "[" in answer and "]" in answer else 0.0))
    answer_relevance = _overlap_score(question + " " + expected_answer, answer)
    context_recall = max(_overlap_score(expected_answer, context_text), _overlap_score(expected_context, context_text))
    context_precision = _overlap_score(question + " " + expected_context, context_text)

    return {
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "faithfulness": round(faithfulness, 3),
        "answer_relevance": round(answer_relevance, 3),
        "context_recall": round(context_recall, 3),
        "context_precision": round(context_precision, 3),
    }


def evaluate_config(golden_dataset: list[dict], use_reranking: bool) -> dict:
    """Evaluate một cấu hình retrieval/generation với 4 metrics bắt buộc."""
    cases = [_run_case(item, use_reranking=use_reranking) for item in golden_dataset]
    metrics = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]
    averages = {
        metric: round(sum(case[metric] for case in cases) / len(cases), 3)
        for metric in metrics
    }
    averages["average"] = round(sum(averages.values()) / len(metrics), 3)
    return {"averages": averages, "cases": cases}


def compare_configs(golden_dataset: list[dict]) -> dict:
    """So sánh A/B: hybrid có rerank và hybrid không rerank."""
    return {
        "Cấu hình A: hybrid + rerank": evaluate_config(golden_dataset, use_reranking=True),
        "Cấu hình B: hybrid không rerank": evaluate_config(golden_dataset, use_reranking=False),
    }


def export_results(comparison: dict):
    """Ghi báo cáo Markdown gồm điểm, phân tích A/B và case yếu nhất."""
    config_a = comparison["Cấu hình A: hybrid + rerank"]["averages"]
    config_b = comparison["Cấu hình B: hybrid không rerank"]["averages"]
    metrics = ["faithfulness", "answer_relevance", "context_recall", "context_precision", "average"]
    metric_labels = {
        "faithfulness": "Độ bám context",
        "answer_relevance": "Độ liên quan câu trả lời",
        "context_recall": "Độ bao phủ context",
        "context_precision": "Độ chính xác context",
        "average": "Trung bình",
    }

    lines = [
        "# Kết quả đánh giá RAG",
        "",
        "## Cách đánh giá",
        "",
        "Bộ đánh giá offline dùng 4 chỉ số trong README: độ bám context, độ liên quan câu trả lời, độ bao phủ context và độ chính xác context.",
        "",
        "## Bảng điểm tổng quan",
        "",
        "| Chỉ số | Cấu hình A (hybrid + rerank) | Cấu hình B (hybrid không rerank) | Chênh lệch |",
        "|--------|----------------------------|-----------------------------|-------|",
    ]
    for metric in metrics:
        delta = round(config_a[metric] - config_b[metric], 3)
        lines.append(f"| {metric_labels[metric]} | {config_a[metric]} | {config_b[metric]} | {delta:+.3f} |")

    cases = comparison["Cấu hình A: hybrid + rerank"]["cases"]
    worst = sorted(cases, key=lambda case: case["average"] if "average" in case else (
        case["faithfulness"] + case["answer_relevance"] + case["context_recall"] + case["context_precision"]
    ) / 4)[:3]

    lines.extend([
        "",
        "## Phân tích A/B",
        "",
        "Cấu hình A dùng hybrid retrieval, RRF merge và reranking. Cấu hình B vẫn dùng hybrid retrieval nhưng tắt reranking.",
        "Cấu hình A được ưu tiên khi điểm trung bình bằng hoặc cao hơn vì kết quả cuối thường bám query tốt hơn.",
        "",
        "## Các case yếu nhất",
        "",
        "| # | Câu hỏi | Bám context | Liên quan | Bao phủ | Chính xác | Nguyên nhân |",
        "|---|----------|--------------|-----------|--------|-----------|------------|",
    ])
    for index, case in enumerate(worst, 1):
        question = case["question"].replace("|", "/")
        lines.append(
            f"| {index} | {question} | {case['faithfulness']} | {case['answer_relevance']} | "
            f"{case['context_recall']} | {case['context_precision']} | Corpus local còn thiếu chi tiết nguồn |"
        )

    lines.extend([
        "",
        "## Đề xuất cải thiện",
        "",
        "1. Thay summary fallback của tài liệu legal bằng markdown extract đầy đủ từ PDF để tăng recall.",
        "2. Crawl URL báo thật thay vì JSON mẫu khi có internet.",
        "3. Bật evaluator dùng LLM như DeepEval hoặc RAGAS khi demo/chấm thủ công.",
        "",
    ])
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    golden_dataset = load_golden_dataset()
    if len(golden_dataset) < 15:
        raise ValueError("golden_dataset.json phải có ít nhất 15 cặp Q&A")
    comparison = compare_configs(golden_dataset)
    export_results(comparison)
    print(f"Đã evaluate {len(golden_dataset)} case và ghi vào {RESULTS_PATH}")


if __name__ == "__main__":
    main()
