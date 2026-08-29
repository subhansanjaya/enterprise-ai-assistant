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
                    "Classify the user's request into exactly one of these "
                    "categories:\n"
                    "- general: casual conversation or questions that do "
                    "not require organizational knowledge.\n"
                    "- knowledge_search: questions that can be answered by "
                    "searching organizational documents.\n"
                    "- research: complex questions requiring investigation "
                    "across multiple documents or sources."
                ),
            },
            *state["messages"],
        ]
    )

    return {
        **state,
        "intent": response.intent,
    }