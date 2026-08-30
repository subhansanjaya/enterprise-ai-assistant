from typing import Literal, TypedDict


Intent = Literal[
    "general",
    "knowledge_search",
    "research",
]


class AgentState(TypedDict):
    messages: list
    user_id: str
    user_roles: list[str]
    research_query: str
    research_new_documents: int
    research_evaluation: dict

    intent: Intent

    retrieved_documents: list
    research_results: list

    research_queries: list[str]
    research_iteration: int

    final_answer: str
