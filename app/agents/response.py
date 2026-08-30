from collections.abc import AsyncIterator

from langchain_openai import ChatOpenAI

from app.agents.citations import validate_citations
from app.agents.state import AgentState
from app.config import settings

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


def build_response_prompt(
    state: AgentState,
) -> list[dict[str, str]]:
    intent = state["intent"]

    if intent == "general":
        return [
            {
                "role": "system",
                "content": (
                    "You are an enterprise AI assistant. "
                    "Respond briefly and naturally to simple interactions "
                    "related to the assistant. "
                    "Explain that you can help users search and investigate "
                    "information from the organization's enterprise "
                    "knowledge base. "
                    "Do not answer unrelated questions."
                ),
            },
            {
                "role": "user",
                "content": state["messages"][-1]["content"],
            },
        ]

    if intent == "out_of_scope":
        return [
            {
                "role": "system",
                "content": (
                    "You are an enterprise AI assistant. "
                    "The user's request is outside the scope of this "
                    "application. "
                    "Respond briefly that the assistant is designed to "
                    "answer questions using the organization's enterprise "
                    "knowledge base and cannot help with unrelated requests. "
                    "Do not answer the user's unrelated question."
                ),
            },
            {
                "role": "user",
                "content": state["messages"][-1]["content"],
            },
        ]

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
            [],
        )

        evidence = "\n\n".join(
            (
                f"Document ID: {document['document_id']}\n"
                f"Document Type: {document['document_type']}\n"
                f"Content:\n{document['content']}"
            )
            for document in documents
        )

    return [
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
                "Citations must use this exact format: [DOCUMENT-ID].\n"
                "Replace DOCUMENT-ID with the actual Document ID from "
                "the supplied evidence.\n"
                "Never write 'DOCUMENT-ID:' inside the brackets.\n"
                "Do not use labels such as [DOCUMENT-ID: ...].\n\n"
                "For knowledge search requests, use the supplied documents "
                "and cite the relevant Document ID.\n\n"
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


async def response_agent(
    state: AgentState,
) -> AgentState:
    prompt = build_response_prompt(state)

    response = await llm.ainvoke(prompt)

    answer = response.content

    if state["intent"] in {
        "knowledge_search",
        "research",
    }:
        allowed_document_ids = {
            document["document_id"]
            for document in state.get(
                "retrieved_documents",
                [],
            )
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


async def stream_response(
    state: AgentState,
) -> AsyncIterator[str]:
    prompt = build_response_prompt(state)

    async for chunk in llm.astream(prompt):
        if chunk.content:
            yield chunk.content