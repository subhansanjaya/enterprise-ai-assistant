from app.agents.graph import route_after_supervisor


def test_routes_knowledge_search_to_retrieval() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_role": "viewer",
        "intent": "knowledge_search",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
    }

    assert route_after_supervisor(state) == "retrieval"


def test_routes_research_to_research_agent() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_role": "analyst",
        "intent": "research",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
    }

    assert route_after_supervisor(state) == "research"


def test_routes_general_to_response() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_role": "viewer",
        "intent": "general",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
    }

    assert route_after_supervisor(state) == "response"
    
def test_unknown_intent_defaults_to_response() -> None:
    state = {
        "messages": [],
        "user_id": "test-user",
        "user_role": "viewer",
        "intent": "general",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
    }

    assert route_after_supervisor(state) == "response"