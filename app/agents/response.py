import asyncio
from collections.abc import AsyncIterator

from langchain_openai import ChatOpenAI

from app.agents.citations import validate_citations
from app.agents.state import AgentState
from app.config import settings

MAX_RESPONSE_LENGTH = 12000


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
                    "You are Commercial Bank's internal enterprise AI "
                    "assistant. "
                    "Respond briefly and naturally to simple interactions "
                    "related to the assistant. "
                    "Explain that you can help authorized employees search "
                    "and investigate information from Commercial Bank's "
                    "enterprise knowledge base. "
                    "Be professional and concise. "
                    "Do not make unsupported claims about Commercial Bank. "
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
                    "You are Commercial Bank's internal enterprise AI "
                    "assistant. "
                    "The user's request is outside the scope of this "
                    "application. "
                    "Respond briefly that the assistant is designed to "
                    "answer questions using Commercial Bank's enterprise "
                    "knowledge base and cannot help with unrelated "
                    "requests. "
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
                "You are Commercial Bank's internal enterprise AI "
                "assistant.\n\n"
                "Answer the user's question using only the supplied "
                "evidence. "
                "Do not invent facts or make unsupported claims about "
                "Commercial Bank.\n\n"
                "Protect Commercial Bank's confidential information and "
                "do not provide information beyond the evidence supplied "
                "for the current authorized user.\n\n"
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
                "say that you do not have enough information.\n\n"
                "Be professional, concise, and appropriate for an "
                "enterprise banking environment."
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


def validate_response(
    answer: str,
    state: AgentState,
) -> None:
    """Validate the generated response before returning it."""
    if not answer.strip():
        raise ValueError(
            "The AI service returned an empty response."
        )

    if len(answer) > MAX_RESPONSE_LENGTH:
        raise ValueError(
            "The AI service returned an unexpectedly long response."
        )

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


async def response_agent(
    state: AgentState,
) -> AgentState:
    retrieval_error = state.get(
        "retrieval_error",
        "",
    )

    if retrieval_error:
        return {
            **state,
            "final_answer": (
                "I'm unable to access the enterprise knowledge base "
                "right now. Please try again later."
            ),
        }

    prompt = build_response_prompt(state)

    try:
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=settings.llm_timeout_seconds,
        )
    except TimeoutError:
        return {
            **state,
            "final_answer": (
                "The AI service took too long to respond. "
                "Please try again later."
            ),
        }
    except Exception as exc:  # noqa: BLE001
        print(
            "LLM ERROR:",
            str(exc),
        )

        return {
            **state,
            "final_answer": (
                "The AI service is currently unavailable. "
                "Please try again later."
            ),
        }

    answer = response.content

    try:
        validate_response(
            answer=answer,
            state=state,
        )
    except ValueError as exc:
        print(
            "LLM RESPONSE VALIDATION ERROR:",
            str(exc),
        )

        return {
            **state,
            "final_answer": (
                "I was unable to produce a valid response. "
                "Please try again."
            ),
        }

    return {
        **state,
        "final_answer": answer,
    }


async def stream_response(
    state: AgentState,
) -> AsyncIterator[str]:
    retrieval_error = state.get(
        "retrieval_error",
        "",
    )

    if retrieval_error:
        yield (
            "I'm unable to access the enterprise knowledge base "
            "right now. Please try again later."
        )
        return

    prompt = build_response_prompt(state)
    answer_parts: list[str] = []

    try:
        async with asyncio.timeout(
            settings.llm_timeout_seconds
        ):
            async for chunk in llm.astream(prompt):
                if chunk.content:
                    answer_parts.append(chunk.content)
                    yield chunk.content

    except TimeoutError:
        yield (
            "The AI service took too long to respond. "
            "Please try again later."
        )
        return

    except Exception as exc:  # noqa: BLE001
        print(
            "LLM STREAM ERROR:",
            str(exc),
        )

        yield (
            "The AI service is currently unavailable. "
            "Please try again later."
        )
        return

    answer = "".join(answer_parts)

    try:
        validate_response(
            answer=answer,
            state=state,
        )
    except ValueError as exc:
        print(
            "LLM STREAM VALIDATION ERROR:",
            str(exc),
        )