from app.agents.query_context import contextualize_query
from app.agents.state import AgentState
from app.rag.service import create_retrieval_service

retrieval_service = create_retrieval_service()


async def retrieval_agent(
    state: AgentState,
) -> AgentState:
    state = await contextualize_query(state)

    query = (
        state.get("contextualized_query", "").strip()
        or state["messages"][-1]["content"]
    )

    try:
        results = await retrieval_service.search(
            query=query,
            top_k=5,
            roles=state["user_roles"],
        )

    except Exception as exc:  # noqa: BLE001
        print(
            "RETRIEVAL ERROR:",
            str(exc),
        )

        return {
            **state,
            "retrieved_documents": [],
            "retrieval_error": (
                "The enterprise knowledge search service "
                "is currently unavailable."
            ),
        }

    print(
        "RETRIEVAL DEBUG:",
        [
            {
                "document_id": result.chunk.document_id,
                "created_date": result.chunk.created_date,
                "hybrid_score": result.hybrid_score,
            }
            for result in results
        ],
    )

    retrieved_documents = [
        {
            "chunk_id": result.chunk.chunk_id,
            "document_id": result.chunk.document_id,
            "document_type": result.chunk.document_type,
            "department": result.chunk.department,
            "access_level": result.chunk.access_level,
            "created_date": result.chunk.created_date,
            "content": result.chunk.content,
            "dense_score": result.dense_score,
            "sparse_score": result.sparse_score,
            "hybrid_score": result.hybrid_score,
        }
        for result in results
    ]

    return {
        **state,
        "retrieved_documents": retrieved_documents,
        "retrieval_error": "",
    }