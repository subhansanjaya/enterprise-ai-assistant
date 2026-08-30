from unittest.mock import AsyncMock, patch

import pytest

from app.agents.research import (
    research_agent,
    route_after_research_evaluation,
)


def make_state() -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": "What caused payment incidents in 2025?",
            }
        ],
        "user_id": "user-1",
        "user_roles": ["viewer"],
        "intent": "research",
        "retrieved_documents": [],
        "research_results": [],
        "research_queries": [],
        "research_iteration": 0,
        "research_query": "",
        "research_new_documents": 0,
        "research_evaluation": {},
        "final_answer": "",
    }


@pytest.mark.asyncio
async def test_research_agent_collects_documents() -> None:
    state = make_state()

    mock_results = [
        {
            "chunk_id": "INC-001-chunk-000",
            "document_id": "INC-001",
            "document_type": "incident",
            "department": "payments",
            "access_level": "internal",
            "created_date": "2025-02-14",
            "content": "Database connection pool exhaustion.",
        }
    ]

    with patch(
        "app.agents.research.mcp_client.search_documents",
        new=AsyncMock(return_value=mock_results),
    ):
        result = await research_agent(state)

    assert result["research_iteration"] == 1
    assert result["research_new_documents"] == 1
    assert result["research_queries"] == [
        "What caused payment incidents in 2025?"
    ]
    assert len(result["retrieved_documents"]) == 1
    assert result["retrieved_documents"][0]["document_id"] == "INC-001"


@pytest.mark.asyncio
async def test_research_agent_deduplicates_documents() -> None:
    state = make_state()

    existing_document = {
        "chunk_id": "INC-001-chunk-000",
        "document_id": "INC-001",
        "document_type": "incident",
        "department": "payments",
        "access_level": "internal",
        "created_date": "2025-02-14",
        "content": "Database connection pool exhaustion.",
    }

    state["retrieved_documents"] = [existing_document]

    with patch(
        "app.agents.research.mcp_client.search_documents",
        new=AsyncMock(return_value=[existing_document]),
    ):
        result = await research_agent(state)

    assert result["research_iteration"] == 1
    assert result["research_new_documents"] == 0
    assert len(result["retrieved_documents"]) == 1


def test_research_stops_when_no_new_documents() -> None:
    state = make_state()

    state["research_iteration"] = 2
    state["research_new_documents"] = 0
    state["research_evaluation"] = {
        "sufficient": False,
        "follow_up_query": "Find more evidence",
    }

    assert route_after_research_evaluation(state) == "response"


def test_research_stops_when_evidence_is_sufficient() -> None:
    state = make_state()

    state["research_iteration"] = 1
    state["research_new_documents"] = 2
    state["research_evaluation"] = {
        "sufficient": True,
        "follow_up_query": "",
    }

    assert route_after_research_evaluation(state) == "response"


def test_research_continues_when_more_evidence_is_needed() -> None:
    state = make_state()

    state["research_iteration"] = 1
    state["research_new_documents"] = 2
    state["research_query"] = "Find payment capacity incidents"
    state["research_evaluation"] = {
        "sufficient": False,
        "follow_up_query": "Find payment capacity incidents",
    }

    assert route_after_research_evaluation(state) == "research"


def test_research_stops_at_max_iterations() -> None:
    state = make_state()

    state["research_iteration"] = 3
    state["research_new_documents"] = 5
    state["research_evaluation"] = {
        "sufficient": False,
        "follow_up_query": "Find more evidence",
    }

    assert route_after_research_evaluation(state) == "response"
