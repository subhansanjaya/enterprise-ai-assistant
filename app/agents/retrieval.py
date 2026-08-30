from app.agents.state import AgentState
from app.rag.service import create_retrieval_service


retrieval_service = create_retrieval_service()


async def retrieval_agent(state: AgentState) -> AgentState:
    query = state["messages"][-1]["content"]

    results = await retrieval_service.search(
        query=query,
        top_k=5,
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
    }