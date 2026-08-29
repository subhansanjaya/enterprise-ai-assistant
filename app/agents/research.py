from app.agents.state import AgentState


async def research_agent(state: AgentState) -> AgentState:
    documents = state.get("retrieved_documents", [])

    research_results = [
        {
            "finding": (
                "Database connection exhaustion appears to be a recurring "
                "cause of payment service failures."
            ),
            "source_documents": [
                document["document_id"]
                for document in documents
            ],
        }
    ]

    return {
        **state,
        "research_results": research_results,
    }