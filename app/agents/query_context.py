from langchain_openai import ChatOpenAI

from app.agents.state import AgentState
from app.config import settings

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


async def contextualize_query(
    state: AgentState,
) -> AgentState:
    messages = state["messages"]

    current_query = messages[-1]["content"]

    if not state.get("requires_context", False):
        return {
            **state,
            "contextualized_query": current_query,
        }

    conversation = "\n".join(
        (
            f"{message['role'].capitalize()}: "
            f"{message['content']}"
        )
        for message in messages
    )

    response = await llm.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "Rewrite the user's latest enterprise knowledge "
                    "question so it can be understood without the "
                    "previous conversation.\n\n"

                    "Resolve references such as 'it', 'its', 'they', "
                    "'that incident', 'the latest one', 'similar incidents', "
                    "or other references to previously discussed entities.\n\n"

                    "Preserve the user's original intent.\n"
                    "Use only information present in the conversation.\n"
                    "Preserve exact document IDs, incident IDs, system names, "
                    "dates, and other important entities when they are "
                    "available in the conversation.\n\n"

                    "Return only the rewritten question. "
                    "Do not answer the question."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Conversation:\n{conversation}\n\n"
                    f"Latest question:\n{current_query}"
                ),
            },
        ]
    )
    

    return {
        **state,
        "contextualized_query": response.content.strip(),
    }