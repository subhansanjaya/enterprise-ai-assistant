from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.config import settings


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)



async def response_agent(state: AgentState) -> AgentState:
    
    documents = state.get("retrieved_documents", [])

    evidence = "\n\n".join(
        (
            f"Document ID: {document['document_id']}\n"
            f"Document Type: {document['document_type']}\n"
            f"Content:\n{document['content']}"
        )
        for document in documents
    )

    prompt = [
        {
            "role": "system",
            "content": (
                "You are an enterprise AI assistant. "
                "Answer the user's question using the supplied evidence. "
                "Do not invent facts that are not supported by the evidence. "
                "When using evidence, cite the Document ID in square brackets, "
                "for example [INC-2025-001]. "
                "If the evidence does not contain enough information, "
                "say that you do not have enough information."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{state['messages'][-1]['content']}\n\n"
                f"Evidence:\n{evidence}"
            ),
        },
    ]

    response = await llm.ainvoke(prompt)

    return {
        **state,
        "final_answer": response.content,
    }