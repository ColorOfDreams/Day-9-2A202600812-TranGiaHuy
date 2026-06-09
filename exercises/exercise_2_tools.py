"""Exercise 2: Add tools and a legal knowledge base entry."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from common.llm import get_llm


LEGAL_KNOWLEDGE = [
    {
        "id": "ucc_breach",
        "keywords": ["breach", "contract", "remedies", "damages", "ucc", "hop dong"],
        "text": (
            "Under the Uniform Commercial Code (UCC) Article 2, remedies for breach of "
            "contract include expectation damages, consequential damages, specific "
            "performance, and cover damages. The statute of limitations is typically "
            "4 years under UCC 2-725."
        ),
    },
    {
        "id": "labor_law_vietnam",
        "keywords": [
            "labor",
            "employment",
            "termination",
            "dismissal",
            "employee",
            "lao dong",
            "sa thai",
            "nguoi lao dong",
        ],
        "text": (
            "Under Vietnam's Labor Code, unilateral termination or dismissal must follow "
            "statutory grounds, notice requirements, and disciplinary procedures. If an "
            "employer terminates unlawfully, remedies may include reinstatement, salary for "
            "the period the employee could not work, social insurance contributions, severance "
            "or additional compensation depending on the facts."
        ),
    },
]


@tool
def search_legal_knowledge(query: str) -> str:
    """Search the small legal knowledge base for relevant legal information."""
    query_lower = query.lower()
    matches = [
        entry
        for entry in LEGAL_KNOWLEDGE
        if any(keyword in query_lower for keyword in entry["keywords"])
    ]
    if not matches:
        return "No relevant legal knowledge entry was found."
    return "\n\n".join(f"[{entry['id']}] {entry['text']}" for entry in matches)


@tool
def check_statute_of_limitations(case_type: str) -> str:
    """Check the typical statute of limitations for a legal claim type."""
    case_lower = case_type.lower()

    if any(keyword in case_lower for keyword in ["contract", "breach", "hop dong"]):
        return (
            "Contract claims: a common US reference point is 4 years under UCC Article 2 "
            "for sale-of-goods contracts. In Vietnam, many civil contract disputes use a "
            "3-year limitation period from the date the claimant knew or should have known "
            "their rights were infringed."
        )
    if any(keyword in case_lower for keyword in ["labor", "employment", "lao dong", "sa thai"]):
        return (
            "Labor disputes in Vietnam often have shorter limitation periods depending on "
            "the dispute type. Individual labor disputes are commonly 1 year from the date "
            "the party discovers the infringement."
        )
    if any(keyword in case_lower for keyword in ["tort", "injury", "negligence", "boi thuong"]):
        return (
            "Tort or civil compensation claims vary by jurisdiction. In Vietnam, many civil "
            "claims use a 3-year limitation period from when the claimant knew or should have "
            "known their rights were infringed."
        )

    return (
        "No exact limitation period found for that case type. Identify the jurisdiction and "
        "claim category, then verify the specific statutory deadline."
    )


async def main():
    load_dotenv()
    llm = get_llm()

    tools = [search_legal_knowledge, check_statute_of_limitations]
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool_item.name: tool_item for tool_item in tools}

    question = "How long is the statute of limitations for a contract breach claim?"

    messages = [
        SystemMessage(
            content=(
                "You are a legal expert. Use the provided tools to look up relevant "
                "information before answering."
            )
        ),
        HumanMessage(content=question),
    ]

    print(f"Question: {question}\n")

    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)

    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Calling tool: {tool_call['name']}")
            selected_tool = tool_map.get(tool_call["name"])
            if selected_tool is None:
                continue

            tool_result = selected_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))

        final_response = await llm_with_tools.ainvoke(messages)
        print(f"\nResult:\n{final_response.content}")
    else:
        print(f"\nResult:\n{response.content}")


if __name__ == "__main__":
    asyncio.run(main())
