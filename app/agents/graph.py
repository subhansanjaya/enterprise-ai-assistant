from langgraph.graph import END, START, StateGraph

from app.agents.research import research_agent
from app.agents.response import response_agent
from app.agents.retrieval import retrieval_agent
from app.agents.state import AgentState
from app.agents.supervisor import supervisor


def route_after_supervisor(state: AgentState) -> str:
    intent = state["intent"]

    if intent == "knowledge_search":
        return "retrieval"

    if intent == "research":
        return "research"

    return "response"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("research", research_agent)
    graph.add_node("response", response_agent)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "retrieval": "retrieval",
            "research": "research",
            "response": "response",
        },
    )

    graph.add_edge("retrieval", "response")
    graph.add_edge("research", "response")
    graph.add_edge("response", END)

    return graph.compile()


agent_graph = build_graph()