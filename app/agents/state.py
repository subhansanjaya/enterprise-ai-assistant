from typing import Literal, TypedDict


Intent = Literal[
    "general",
    "knowledge_search",
    "research",
]


class AgentState(TypedDict):
    messages: list
    user_id: str
    user_role: str

    intent: Intent

    retrieved_documents: list
    research_results: list

    final_answer: str