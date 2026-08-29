from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.graph import agent_graph


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "demo-user"
    user_role: str = "viewer"


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    state = {
        "messages": [
            {
                "role": "user",
                "content": request.message,
            }
        ],
        "user_id": request.user_id,
        "user_role": request.user_role,
        "intent": "",
        "final_answer": "",
    }

    result = await agent_graph.ainvoke(state)

    return ChatResponse(
        answer=result["final_answer"],
    )