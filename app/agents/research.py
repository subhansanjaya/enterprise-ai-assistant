from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.query_context import contextualize_query
from app.agents.state import AgentState
from app.config import settings
from app.mcp.client import MCPClient

MAX_RESEARCH_ITERATIONS = 3


llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=settings.openai_api_key,
    temperature=0,
)


mcp_client = MCPClient()


class ResearchFinding(BaseModel):
    finding: str
    source_documents: list[str]


class ResearchEvaluation(BaseModel):
    sufficient: bool
    follow_up_query: str
    findings: list[ResearchFinding]


class AnalysisDecision(BaseModel):
    required: bool
    operation: Literal[
        "count",
        "group_by",
        "percentage",
        "latest",
        "earliest",
    ]
    field: str


async def determine_analysis(
    question: str,
) -> AnalysisDecision:
    evaluator = llm.with_structured_output(
        AnalysisDecision
    )

    response = await evaluator.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "Determine whether the enterprise question requires "
                    "structured analysis of retrieved documents.\n\n"
                    "Use analysis when the question asks for counting, "
                    "grouping, percentages, or identifying the latest "
                    "or earliest record.\n\n"
                    "If structured analysis is not required, set required=false.\n\n"
                    "Choose exactly one operation:\n"
                    "- count\n"
                    "- group_by\n"
                    "- percentage\n"
                    "- latest\n"
                    "- earliest\n\n"
                    "For group_by or percentage, identify the relevant "
                    "document field.\n\n"
                    "For latest or earliest, use created_date.\n\n"
                    "Do not answer the question."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ]
    )

    return response


async def research_agent(
    state: AgentState,
) -> AgentState:
    state = await contextualize_query(state)

    original_query = (
        state.get("contextualized_query", "").strip()
        or state["messages"][-1]["content"]
    )

    research_query = (
        state.get("research_query", "").strip()
        or original_query
    )

    results = await mcp_client.search_documents(
        query=research_query,
        roles=state["user_roles"],
        top_k=5,
    )

    existing_documents = state.get(
        "retrieved_documents",
        [],
    )

    existing_ids = {
        document["chunk_id"]
        for document in existing_documents
    }

    new_documents = [
        document
        for document in results
        if document["chunk_id"] not in existing_ids
    ]

    new_document_count = len(new_documents)

    retrieved_documents = [
        *existing_documents,
        *new_documents,
    ]

    research_queries = [
        *state.get("research_queries", []),
        research_query,
    ]

    research_iteration = (
        state.get("research_iteration", 0) + 1
    )

    research_results = [
        {
            "finding": document["content"],
            "source_documents": [
                document["document_id"],
            ],
        }
        for document in retrieved_documents
    ]

    analysis_result = state.get(
        "analysis_result",
        {},
    )

    if retrieved_documents:
        analysis_decision = await determine_analysis(
            original_query
        )

        if analysis_decision.required:
            try:
                analysis_result = (
                    await mcp_client.analyze_documents(
                        documents=retrieved_documents,
                        operation=analysis_decision.operation,
                        field=analysis_decision.field,
                    )
                )
            except RuntimeError as exc:
                print(
                    "ANALYSIS ERROR:",
                    str(exc),
                )

    return {
        **state,
        "retrieved_documents": retrieved_documents,
        "research_results": research_results,
        "research_queries": research_queries,
        "research_iteration": research_iteration,
        "research_new_documents": new_document_count,
        "analysis_result": analysis_result,
    }


async def evaluate_research(
    state: AgentState,
) -> AgentState:
    documents = state.get(
        "retrieved_documents",
        [],
    )

    evidence = "\n\n".join(
        (
            f"Document ID: {document['document_id']}\n"
            f"Document Type: {document['document_type']}\n"
            f"Content:\n{document['content']}"
        )
        for document in documents
    )

    previous_queries = "\n".join(
        f"- {query}"
        for query in state.get(
            "research_queries",
            [],
        )
    )

    research_question = (
        state.get("contextualized_query", "").strip()
        or state["messages"][-1]["content"]
    )

    evaluator = llm.with_structured_output(
        ResearchEvaluation
    )

    response = await evaluator.ainvoke(
        [
            {
                "role": "system",
                "content": (
                    "You evaluate whether an enterprise research question "
                    "has enough evidence to answer reliably.\n\n"
                    "Review the supplied documents and previous search queries.\n\n"
                    "Produce concise research findings based only on the "
                    "supplied evidence. Each finding must identify the "
                    "Document IDs that support it.\n\n"
                    "If the evidence is sufficient to answer the research "
                    "question reliably, set sufficient=true and leave "
                    "follow_up_query empty.\n\n"
                    "If the evidence is insufficient, set sufficient=false "
                    "and provide ONE focused follow-up search query that "
                    "targets genuinely missing information.\n\n"
                    "IMPORTANT:\n"
                    "- Do not invent facts.\n"
                    "- Do not create findings unsupported by the evidence.\n"
                    "- Every finding must have at least one supporting "
                    "Document ID.\n"
                    "- Use exact Document IDs from the supplied evidence.\n"
                    "- Do not repeat or paraphrase a previous search query.\n"
                    "- Do not request information already present in the "
                    "evidence.\n"
                    "- If additional searches are unlikely to provide "
                    "materially different evidence, set sufficient=true."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Research question:\n"
                    f"{research_question}\n\n"
                    f"Previous search queries:\n"
                    f"{previous_queries}\n\n"
                    f"Evidence collected so far:\n"
                    f"{evidence}\n\n"
                    f"Structured analysis:\n"
                    f"{state.get('analysis_result', {})}"
                ),
            },
        ]
    )

    return {
        **state,
        "research_results": [
            finding.model_dump()
            for finding in response.findings
        ],
        "research_evaluation": {
            "sufficient": response.sufficient,
            "follow_up_query": response.follow_up_query.strip(),
        },
        "research_query": response.follow_up_query.strip(),
    }


def route_after_research_evaluation(
    state: AgentState,
) -> Literal["research", "response"]:
    if state["research_new_documents"] == 0:
        return "response"

    if state["research_iteration"] >= MAX_RESEARCH_ITERATIONS:
        return "response"

    evaluation = state.get(
        "research_evaluation",
        {},
    )

    if evaluation.get("sufficient", False):
        return "response"

    follow_up_query = state.get(
        "research_query",
        "",
    ).strip()

    if not follow_up_query:
        return "response"

    return "research"