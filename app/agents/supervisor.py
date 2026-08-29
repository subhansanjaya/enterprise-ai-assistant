from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.state import AgentState
from app.config import settings


class RoutingDecision(BaseModel):
    intent: Literal[
        "general",
        "knowledge_search",
        "research",
    ]


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def supervisor(state: AgentState) -> AgentState:

    structured_llm = llm.with_structured_output(RoutingDecision)

    response = await structured_llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "You are the supervisor of an enterprise AI assistant. "
                    "Classify the user's request into exactly one of these categories:\n\n"

                    "general: Casual conversation or questions that do not require "
                    "organizational knowledge.\n\n"

                    "knowledge_search: Questions that can be answered by retrieving "
                    "information from the organization's existing documents. Use this "
                    "for questions about incidents, systems, architecture, procedures, "
                    "policies, specifications, or other known organizational information.\n\n"

                    "research: Complex questions that require investigation across "
                    "multiple pieces of evidence, comparison of findings, synthesis "
                    "across documents, or iterative research. Use this when a simple "
                    "document lookup is not sufficient.\n\n"

                    "Examples:\n"
                    "- 'What caused the payment gateway failure?' → knowledge_search\n"
                    "- 'What is the payment API architecture?' → knowledge_search\n"
                    "- 'What steps are in the payment gateway recovery procedure?' "
                    "→ knowledge_search\n"
                    "- 'What recurring factors caused payment incidents in 2025?' "
                    "→ research\n"
                    "- 'Compare the payment incidents and recommend preventive actions.' "
                    "→ research"
                )
            },
            *state["messages"],
        ]
    )

    return {
        **state,
        "intent": response.intent,
    }