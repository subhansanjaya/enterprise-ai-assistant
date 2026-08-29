from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentState
from app.agents.supervisor import supervisor
from app.agents.response import response_agent


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor)
    graph.add_node("response", response_agent)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "response")
    graph.add_edge("response", END)

    return graph.compile()


agent_graph = build_graph()