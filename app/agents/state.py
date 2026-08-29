from typing import TypedDict


class AgentState(TypedDict):
    messages: list
    user_id: str
    user_role: str
    intent: str
    final_answer: str