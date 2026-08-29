from langchain_openai import ChatOpenAI

from app.config import settings
from app.agents.state import AgentState


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def supervisor(state: AgentState) -> AgentState:
    response = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "You are the supervisor of an enterprise AI assistant. "
                    "Understand the user's request and provide a concise intent "
                    "classification. For now, classify requests as "
                    "'general' unless they clearly require another capability."
                ),
            },
            *state["messages"],
        ]
    )

    return {
        **state,
        "intent": response.content,
    }