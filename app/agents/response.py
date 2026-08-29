from langchain_openai import ChatOpenAI

from app.config import settings
from app.agents.state import AgentState


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def response_agent(state: AgentState) -> AgentState:
    response = await llm.ainvoke(state["messages"])

    return {
        **state,
        "final_answer": response.content,
    }