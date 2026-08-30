from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.config import settings
from app.agents.citations import validate_citations

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def response_agent(state: AgentState) -> AgentState:
    intent = state["intent"]

    if intent == "research":
        research_results = state.get(
            "research_results",
            [],
        )

        evidence = "\n\n".join(
            (
                f"Finding: {result['finding']}\n"
                f"Source Documents: "
                f"{', '.join(result['source_documents'])}"
            )
            for result in research_results
        )

    else:
        documents = state.get(
            "retrieved_documents",
            []
        )

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
                "Answer the user's question using only the supplied evidence. "
                "Do not invent facts.\n\n"

                "For research requests, use the supplied research findings "
                "and their source documents. "
                "Only cite Document IDs that appear in the supplied "
                "source documents.\n\n"

                "For knowledge search requests, use the supplied documents "
                "and cite the relevant Document ID.\n\n"

                "Citations must use this format: [DOCUMENT-ID].\n\n"

                "If the evidence does not contain enough information, "
                "say that you do not have enough information."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n"
                f"{state['messages'][-1]['content']}\n\n"
                f"Evidence:\n"
                f"{evidence}"
            ),
        },
    ]

    response = await llm.ainvoke(prompt)
    
    answer = response.content

    allowed_document_ids = {
        document["document_id"]
        for document in state.get("retrieved_documents", [])
    }

    invalid_citations = validate_citations(
        answer,
        allowed_document_ids,
    )

    if invalid_citations:
        raise ValueError(
            "Response contains invalid document citations: "
            + ", ".join(invalid_citations)
        )

    return {
        **state,
        "final_answer": answer,     
    }

