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
        "out_of_scope",
    ]
    requires_context: bool


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def supervisor(
    state: AgentState,
) -> AgentState:
    structured_llm = llm.with_structured_output(
        RoutingDecision
    )

    response = await structured_llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "You are the supervisor of an enterprise AI assistant. "
                    "Classify the user's request into exactly one category "
                    "and determine whether the latest question depends on "
                    "previous conversation context.\n\n"

                    "Categories:\n\n"

                    "general: Casual conversation or questions that do not "
                    "require organizational knowledge.\n\n"

                    "knowledge_search: Questions that can be answered by "
                    "retrieving information from the organization's existing "
                    "documents. Use this for questions about incidents, "
                    "systems, architecture, procedures, policies, "
                    "specifications, or other known organizational information.\n\n"

                    "research: Complex questions that require investigation "
                    "across multiple pieces of evidence, comparison of "
                    "findings, synthesis across documents, or iterative "
                    "research.\n\n"

                    "out_of_scope: Questions unrelated to the organization's "
                    "enterprise knowledge base or capabilities.\n\n"

                    "requires_context:\n"
                    "Set true when the latest question depends on previous "
                    "conversation content to understand its meaning. "
                    "Examples include references such as 'it', 'its', "
                    "'they', 'that incident', 'the most recent one', "
                    "'similar incidents', 'what about that', or other "
                    "references to previously discussed entities.\n\n"

                    "Set false when the latest question is sufficiently "
                    "self-contained and can be understood without previous "
                    "conversation context.\n\n"

                    "Examples:\n"
                    "- 'What caused the payment gateway failure?' → "
                    "knowledge_search, requires_context=false\n"
                    "- 'What is the payment API architecture?' → "
                    "knowledge_search, requires_context=false\n"
                    "- 'What recurring factors caused payment incidents "
                    "in 2025?' → research, requires_context=false\n"
                    "- 'Which was the most recent?' → "
                    "knowledge_search, requires_context=true\n"
                    "- 'What was its root cause?' → "
                    "knowledge_search, requires_context=true\n"
                    "- 'Were there any similar incidents?' → "
                    "knowledge_search, requires_context=true\n"
                    "- 'What is the capital of France?' → "
                    "out_of_scope, requires_context=false"
                ),
            },
            *state["messages"],
        ]
    )

    return {
        **state,
        "intent": response.intent,
        "requires_context": response.requires_context,
    }