from app.agents.state import AgentState


async def retrieval_agent(state: AgentState) -> AgentState:
    documents = [
        {
            "document_id": "INC-2025-001",
            "title": "Payment Gateway Incident",
            "content": (
                "The payment gateway experienced intermittent failures "
                "caused by database connection exhaustion."
            ),
        },
        {
            "document_id": "RUN-2025-004",
            "title": "Payment Gateway Recovery Runbook",
            "content": (
                "The recovery procedure includes checking database "
                "connection pools and restarting affected services."
            ),
        },
    ]

    return {
        **state,
        "retrieved_documents": documents,
    }