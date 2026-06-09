"""Exercise 4: Add a Privacy Agent to the multi-agent system."""

import asyncio
import os
import sys
from typing import Annotated, TypedDict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from common.llm import get_llm


def _last_wins(left: str | None, right: str | None) -> str:
    """Reducer for parallel branches: the newest non-empty value wins."""
    return right if right is not None else (left or "")


class State(TypedDict):
    question: str
    law_analysis: Annotated[str, _last_wins]
    tax_analysis: Annotated[str, _last_wins]
    compliance_analysis: Annotated[str, _last_wins]
    privacy_analysis: Annotated[str, _last_wins]
    needs_tax: bool
    needs_compliance: bool
    needs_privacy: bool
    final_response: str


def law_agent(state: State) -> dict:
    """General legal analysis agent."""
    llm = get_llm()
    prompt = f"""You are a legal expert. Analyze the question below:

{state['question']}

Focus on contracts, civil liability, legal rights, and legal obligations."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"law_analysis": response.content}


def check_routing(state: State) -> dict:
    """Decide which specialist agents should be called."""
    question_lower = state["question"].lower()

    needs_tax = any(
        keyword in question_lower
        for keyword in ["tax", "irs", "revenue", "thuế", "thue"]
    )
    needs_compliance = any(
        keyword in question_lower
        for keyword in ["compliance", "sec", "regulation", "sox", "aml", "fCPA".lower()]
    )
    needs_privacy = any(
        keyword in question_lower
        for keyword in [
            "data",
            "privacy",
            "gdpr",
            "ccpa",
            "breach",
            "personal information",
            "du lieu",
            "bao mat",
        ]
    )

    return {
        "needs_tax": needs_tax,
        "needs_compliance": needs_compliance,
        "needs_privacy": needs_privacy,
    }


def route_to_specialists(state: State) -> list[Send]:
    """Dispatch selected specialist agents in parallel."""
    tasks: list[Send] = []

    if state.get("needs_tax"):
        tasks.append(Send("tax_agent", state))
    if state.get("needs_compliance"):
        tasks.append(Send("compliance_agent", state))
    if state.get("needs_privacy"):
        tasks.append(Send("privacy_agent", state))

    return tasks if tasks else [Send("aggregate_results", state)]


def tax_agent(state: State) -> dict:
    """Tax specialist agent."""
    llm = get_llm()
    prompt = f"""You are a tax expert. Analyze the tax aspect of this question:

Question: {state['question']}
General legal analysis: {state.get('law_analysis', 'N/A')}

Focus on IRS exposure, tax evasion, penalties, FBAR, FATCA, back taxes, and interest."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"tax_analysis": response.content}


def compliance_agent(state: State) -> dict:
    """Regulatory compliance specialist agent."""
    llm = get_llm()
    prompt = f"""You are a regulatory compliance expert. Analyze the compliance aspect:

Question: {state['question']}
General legal analysis: {state.get('law_analysis', 'N/A')}

Focus on SEC, SOX, FCPA, AML, governance controls, and regulatory violations."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"compliance_analysis": response.content}


def privacy_agent(state: State) -> dict:
    """Privacy and data-protection specialist agent."""
    llm = get_llm()
    prompt = f"""You are a privacy and data-protection lawyer. Analyze the privacy aspect:

Question: {state['question']}
General legal analysis: {state.get('law_analysis', 'N/A')}

Focus on GDPR, CCPA, data breach notification, consent, data minimization, privacy rights,
regulatory fines, customer notification, and remediation steps."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"privacy_analysis": response.content}


def aggregate_results(state: State) -> dict:
    """Aggregate all available agent analyses into one final response."""
    llm = get_llm()

    sections = []
    if state.get("law_analysis"):
        sections.append(f"LEGAL ANALYSIS:\n{state['law_analysis']}")
    if state.get("tax_analysis"):
        sections.append(f"TAX ANALYSIS:\n{state['tax_analysis']}")
    if state.get("compliance_analysis"):
        sections.append(f"COMPLIANCE ANALYSIS:\n{state['compliance_analysis']}")
    if state.get("privacy_analysis"):
        sections.append(f"PRIVACY ANALYSIS:\n{state['privacy_analysis']}")

    combined = "\n\n".join(sections)

    prompt = f"""Synthesize the following specialist analyses into a concise legal report:

{combined}

Original question: {state['question']}

Create a short, clearly structured report and include a brief educational-use disclaimer."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_response": response.content}


def build_graph() -> StateGraph:
    """Build the multi-agent graph."""
    graph = StateGraph(State)

    graph.add_node("law_agent", law_agent)
    graph.add_node("check_routing", check_routing)
    graph.add_node("tax_agent", tax_agent)
    graph.add_node("compliance_agent", compliance_agent)
    graph.add_node("privacy_agent", privacy_agent)
    graph.add_node("aggregate_results", aggregate_results)

    graph.add_edge(START, "law_agent")
    graph.add_edge("law_agent", "check_routing")
    graph.add_conditional_edges(
        "check_routing",
        route_to_specialists,
        ["tax_agent", "compliance_agent", "privacy_agent", "aggregate_results"],
    )
    graph.add_edge("tax_agent", "aggregate_results")
    graph.add_edge("compliance_agent", "aggregate_results")
    graph.add_edge("privacy_agent", "aggregate_results")
    graph.add_edge("aggregate_results", END)

    return graph.compile()


async def main():
    load_dotenv()

    question = (
        "A company suffered a customer data breach, failed to notify users, and hid "
        "overseas revenue from tax authorities. What are the legal consequences?"
    )

    print("=" * 70)
    print("MULTI-AGENT SYSTEM WITH PRIVACY AGENT")
    print("=" * 70)
    print(f"\nQuestion: {question}\n")
    print("Processing through agents...\n")

    graph = build_graph()

    result = await graph.ainvoke(
        {
            "question": question,
            "law_analysis": "",
            "tax_analysis": "",
            "compliance_analysis": "",
            "privacy_analysis": "",
            "needs_tax": False,
            "needs_compliance": False,
            "needs_privacy": False,
            "final_response": "",
        }
    )

    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(result["final_response"])
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
