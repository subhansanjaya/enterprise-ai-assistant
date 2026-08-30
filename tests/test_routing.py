from app.agents.graph import (
    route_after_context,
    route_after_supervisor,
)


def test_routes_knowledge_search_to_query_context() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_roles": ["viewer"],
        "intent": "knowledge_search",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
        "research_evaluation": {},
    }

    assert route_after_supervisor(state) == "query_context"


def test_routes_research_to_query_context() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_roles": ["analyst"],
        "intent": "research",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
        "research_evaluation": {},
    }

    assert route_after_supervisor(state) == "query_context"


def test_routes_knowledge_search_from_context_to_retrieval() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_roles": ["viewer"],
        "intent": "knowledge_search",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
        "research_evaluation": {},
    }

    assert route_after_context(state) == "retrieval"


def test_routes_research_from_context_to_research_agent() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_roles": ["analyst"],
        "intent": "research",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
        "research_evaluation": {},
    }

    assert route_after_context(state) == "research"