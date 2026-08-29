from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agents.graph import agent_graph
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


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
        "user_role": current_user.primary_role,
        "intent": "general",
        "retrieved_documents": [],
        "research_results": [],
        "final_answer": "",
    }

    result = await agent_graph.ainvoke(state)

    return ChatResponse(
        answer=result["final_answer"],
    )