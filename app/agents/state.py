from typing import Literal, TypedDict

Intent = Literal[
    "general",
    "knowledge_search",
    "research",
    "out_of_scope",
]


class AgentState(TypedDict):
    messages: list[dict[str, str]]
    user_id: str
    user_roles: list[str]

    contextualized_query: str
    requires_context: bool

    research_query: str
    research_new_documents: int
    research_evaluation: dict

    intent: Intent

    retrieved_documents: list
    research_results: list

    research_queries: list[str]
    research_iteration: int

    final_answer: str