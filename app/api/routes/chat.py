from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.graph import (
    agent_graph,
    preparation_graph,
)
from app.agents.response import stream_response
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser
from app.db.database import get_db
from app.db.repository import (
    add_message,
    create_conversation,
    get_conversation,
    get_messages,
)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class Source(BaseModel):
    document_id: str
    document_type: str
    department: str
    access_level: str
    created_date: str


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[Source]


def build_state(
    messages: list[dict[str, str]],
    current_user: AuthenticatedUser,
) -> dict:
    return {
        "messages": messages,
        "user_id": current_user.user_id,
        "user_roles": current_user.roles,
        "contextualized_query": "",
        "requires_context": False,
        "research_query": "",
        "research_queries": [],
        "research_iteration": 0,
        "intent": "general",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
        "research_new_documents": 0,
        "research_evaluation": {},
    }


def load_conversation(
    db: Session,
    request: ChatRequest,
    current_user: AuthenticatedUser,
):
    if request.conversation_id:
        conversation = get_conversation(
            db=db,
            conversation_id=request.conversation_id,
            user_id=current_user.user_id,
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found.",
            )
    else:
        conversation = create_conversation(
            db=db,
            user_id=current_user.user_id,
            title=request.message[:100],
        )

    return conversation


def prepare_messages(
    db: Session,
    conversation,
    request: ChatRequest,
) -> list[dict[str, str]]:
    previous_messages = get_messages(
        db=db,
        conversation=conversation,
    )

    add_message(
        db=db,
        conversation=conversation,
        role="user",
        content=request.message,
    )

    messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in previous_messages
    ]

    messages.append(
        {
            "role": "user",
            "content": request.message,
        }
    )

    return messages


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ChatResponse:

    conversation = load_conversation(
        db=db,
        request=request,
        current_user=current_user,
    )

    messages = prepare_messages(
        db=db,
        conversation=conversation,
        request=request,
    )

    state = build_state(
        messages=messages,
        current_user=current_user,
    )

    result = await agent_graph.ainvoke(state)

    answer = result["final_answer"]

    add_message(
        db=db,
        conversation=conversation,
        role="assistant",
        content=answer,
    )

    sources = [
        Source(
            document_id=document["document_id"],
            document_type=document["document_type"],
            department=document["department"],
            access_level=document["access_level"],
            created_date=document["created_date"],
        )
        for document in result.get(
            "retrieved_documents",
            [],
        )
    ]

    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        sources=sources,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> StreamingResponse:

    conversation = load_conversation(
        db=db,
        request=request,
        current_user=current_user,
    )

    messages = prepare_messages(
        db=db,
        conversation=conversation,
        request=request,
    )

    state = build_state(
        messages=messages,
        current_user=current_user,
    )

    async def event_stream() -> AsyncIterator[str]:
        prepared_state = await preparation_graph.ainvoke(
            state
        )


        answer_parts: list[str] = []

        async for chunk in stream_response(
            prepared_state
        ):
            answer_parts.append(chunk)

            yield (
                "event: token\n"
                f"data: {chunk}\n\n"
            )

        answer = "".join(answer_parts)

        add_message(
            db=db,
            conversation=conversation,
            role="assistant",
            content=answer,
        )

        yield (
            "event: metadata\n"
            f"data: {conversation.id}\n\n"
        )

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )