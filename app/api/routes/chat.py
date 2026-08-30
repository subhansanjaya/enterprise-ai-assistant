from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agents.graph import agent_graph
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class Source(BaseModel):
    document_id: str
    document_type: str
    department: str
    access_level: str
    created_date: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: AuthenticatedUser = Depends(
        get_current_user
    ),
) -> ChatResponse:
    state = {
        "messages": [
            {
                "role": "user",
                "content": request.message,
            }
        ],
        "user_id": current_user.user_id,
        "user_roles": current_user.roles,
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

    unique_sources = {}

    for document in result.get("retrieved_documents", []):
        document_id = document["document_id"]

        if document_id not in unique_sources:
            unique_sources[document_id] = Source(
                document_id=document_id,
                document_type=document["document_type"],
                department=document["department"],
                access_level=document["access_level"],
                created_date=document["created_date"],
            )

    sources = list(unique_sources.values())

    return ChatResponse(
        answer=result["final_answer"],
        sources=sources,
    )