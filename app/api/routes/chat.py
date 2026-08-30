from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.graph import agent_graph
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


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
) -> ChatResponse:

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

    state = {
        "messages": messages,
        "user_id": current_user.user_id,
        "user_roles": current_user.roles,
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
        for document in result.get("retrieved_documents", [])
    ]

    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        sources=sources,
    )