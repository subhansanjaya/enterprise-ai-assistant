# Enterprise AI Assistant

An enterprise-focused AI assistant for authenticated users to search and investigate information from an organization's internal knowledge base.

The application combines hybrid Retrieval-Augmented Generation (RAG), role-based access control, LangGraph-based agent orchestration, conversational context, citation validation, MCP integration, structured analysis, streaming responses, rate limiting, failure handling, and LangSmith observability.

![screenshot](https://github.com/subhansanjaya/enterprise-ai-assistant/blob/main/assets/capture1.png)
![screenshot](https://github.com/subhansanjaya/enterprise-ai-assistant/blob/main/assets/capture2.png)
![screenshot](https://github.com/subhansanjaya/enterprise-ai-assistant/blob/main/assets/capture3.png)

## Key Features

- **Enterprise Knowledge Search** — semantic search with embeddings and Pinecone, BM25 keyword retrieval, and hybrid ranking.
- **Role-Based Access Control** — Keycloak authentication, JWT validation, and retrieval-time document access filtering.
- **Multi-Agent Workflow** — supervisor routing, knowledge search, research, research evaluation, and iterative follow-up searches.
- **Conversational Context** — PostgreSQL conversation persistence and contextualized follow-up questions.
- **Citations** — answers cite supporting enterprise documents using document IDs, with citation validation.
- **Streaming** — responses can be streamed incrementally to the Streamlit interface.
- **MCP Integration** — a narrowly scoped MCP client/server boundary for enterprise document search.
- **Structured Analysis** — deterministic analysis capabilities for structured enterprise data.
- **Rate Limiting** — per-user token-bucket rate limiting at the API boundary.
- **Failure Handling** — controlled handling of LLM, retrieval, MCP, timeout, validation, and authorization failures.
- **Observability** — LangSmith tracing and a user-facing Streamlit activity view.
- **Out-of-Scope Handling** — unrelated requests are identified and rejected rather than answered using external knowledge.

## Architecture

```text
                           ┌──────────────────────┐
                           │        User          │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │      Streamlit       │
                           │   Chat + Activity    │
                           └──────────┬───────────┘
                                      │ HTTP / SSE
                                      ▼
                           ┌──────────────────────┐
                           │       FastAPI        │
                           │ Auth / Validation    │
                           │ Rate Limiting        │
                           │ Error Handling       │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │      LangGraph       │
                           │      Supervisor      │
                           └──────────┬───────────┘
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                   Context      Retrieval      Research
                    Agent         Agent          Agent
                         │            │            │
                         │            ▼            ▼
                         │        Hybrid RAG    MCP Search
                         │            │            │
                         └────────────┴────────────┘
                                      │
                                      ▼
                               Response Agent
                                      │
                                      ▼
                               Citation Validation
                                      │
                                      ▼
                                  Final Answer

       ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
       │   Pinecone     │   │  PostgreSQL    │   │  LangSmith     │
       │ Vector Search  │   │ Conversations  │   │  Observability │
       └────────────────┘   └────────────────┘   └────────────────┘
```

## Agent Workflow

### Knowledge Search

```text
User question
    ↓
Supervisor
    ↓
Contextualization when required
    ↓
Hybrid Retrieval
    ↓
Response Generation
    ↓
Citation Validation
    ↓
Answer
```

### Research

```text
User question
    ↓
Supervisor
    ↓
Contextualization when required
    ↓
Research Agent
    ↓
MCP / enterprise search
    ↓
Structured analysis when appropriate
    ↓
Research Evaluator
    ↓
More evidence required? ── Yes ──→ Follow-up search
    │
    No
    ↓
Response Agent
    ↓
Answer
```

Research is bounded by a configured maximum number of iterations.

## Authentication and Authorization

Authentication is handled through Keycloak using OpenID Connect. The FastAPI backend validates the authenticated user's access token.

Document access is controlled through role-based access levels:

| Role | Access |
|---|---|
| `viewer` | `internal` |
| `analyst` | `internal`, `restricted` |
| `admin` | `internal`, `restricted`, `confidential` |

Access filtering is applied during retrieval so users cannot retrieve documents outside their permitted access level.

## Retrieval

The application uses hybrid retrieval.

### Dense Retrieval

User queries are converted into embeddings and searched against Pinecone.

### Sparse Retrieval

BM25 provides keyword-based retrieval, which is useful for exact terms such as incident IDs, system names, technical terminology, and error messages.

### Hybrid Ranking

Dense and sparse scores are normalized and combined:

```text
hybrid_score = 0.7 × dense_score + 0.3 × sparse_score
```

The highest-ranked authorized evidence is supplied to the response workflow.

## MCP Integration

The application uses a streamable HTTP MCP client to communicate with the MCP server.

```text
Research Agent
       │
       ▼
   MCP Client
       │
       │ Streamable HTTP
       ▼
   MCP Server
       │
       ├── search_documents
       │
       └── analyze_documents
```

The MCP boundary validates:

- non-empty queries
- known user roles
- `top_k` limits
- access filters
- supported analysis operations

The MCP client applies a configurable timeout and converts dependency failures into controlled application errors.

## Structured Analysis

The MCP analysis tool provides constrained deterministic operations over retrieved documents:

- `count`
- `group_by`
- `percentage`
- `latest`
- `earliest`

The analysis operates on documents already retrieved for the request rather than allowing arbitrary user-supplied Python execution.

This is especially useful for questions such as:

```text
How many payment incidents occurred in 2025?
Which incident was the most recent?
What percentage of incidents belong to each category?
```

## Conversation Context

Conversation messages are persisted in PostgreSQL. The supervisor determines whether a question depends on previous conversation context.

For example:

```text
User: What payment incidents happened in 2025?
Assistant: ... INC-2025-001 ... INC-2025-017
User: Which was the most recent?
```

The contextualization agent transforms the follow-up into a self-contained query such as:

```text
What was the most recent payment incident reported in 2025?
```

This allows references such as "it", "its", "the latest one", "that incident", and "similar incidents" to be resolved from conversation history.

## Citations

Knowledge-based responses are required to cite enterprise documents using their document IDs.

Example:

```text
The most recent incident occurred on 22 May 2025 [INC-2025-017].
```

Generated citations are validated against documents actually retrieved for the request.

## Rate Limiting

The API uses a per-user token-bucket rate limiter.

```text
Request
   │
   ▼
Token Bucket
   │
   ├── Token available → Continue
   │
   └── No token → Controlled rejection
```

Capacity and refill behavior are configurable.

## Error Handling

External dependencies are treated as explicit failure boundaries.

Examples include:

```text
LLM Failure
    ↓
Controlled application error

Pinecone Failure
    ↓
Retrieval failure / graceful handling

MCP Failure
    ↓
Informative tool failure

MCP Timeout
    ↓
Controlled timeout error

Invalid Request
    ↓
Validation error

Unauthorized Tool
    ↓
Authorization rejection
```

Internal exceptions and implementation details should not be exposed directly to users.

## Observability

LangSmith tracing can be enabled through environment configuration.

The system is designed to make important execution steps observable, including:

- supervisor routing
- contextualization
- retrieval
- research iterations
- MCP calls
- structured analysis
- response generation
- citation validation

The Streamlit interface provides a simplified user-facing execution view rather than exposing internal reasoning or chain-of-thought.

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

### AI / Agent Orchestration

- LangGraph
- LangChain
- OpenAI

### Retrieval

- Pinecone
- BM25 / `rank-bm25`
- Hybrid retrieval
- Embeddings

### Authentication

- Keycloak
- OpenID Connect
- JWT

### Frontend

- Streamlit

### Integration / Tools

- MCP
- Structured Python analysis

### Development

- Pytest
- Ruff

## Project Structure

```text
enterprise-ai-assistant/
├── app/
│   ├── agents/
│   │   ├── graph.py
│   │   ├── supervisor.py
│   │   ├── query_context.py
│   │   ├── retrieval.py
│   │   ├── research.py
│   │   ├── response.py
│   │   └── state.py
│   ├── api/
│   │   ├── routes/
│   │   └── rate_limit.py
│   ├── auth/
│   ├── db/
│   ├── rag/
│   └── mcp/
├── mcp_server/
├── data/
├── specs/
│   ├── 001-foundation.md
│   ├── 002-production-hardening.md
│   └── 003-research-and-analysis.md
├── tests/
├── evals/
├── streamlit_app.py
├── architecture.md
├── pyproject.toml
└── README.md
```

## Setup

### Requirements

- Python 3.11 or 3.12
- PostgreSQL
- Keycloak
- Pinecone account/index
- OpenAI API key

### Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key

PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=enterprise-ai-assistant
PINECONE_NAMESPACE=internal

KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=enterprise-ai
KEYCLOAK_CLIENT_ID=backend-api
KEYCLOAK_UI_CLIENT_ID=enterprise-ai-ui

MCP_SERVER_URL=http://127.0.0.1:8001/mcp

DATABASE_URL=postgresql+psycopg://keycloak:keycloak@localhost:5433/enterprise_ai

EMBEDDING_MODEL=text-embedding-3-small
```

For optional LangSmith tracing:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=enterprise-ai-assistant
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

**Never commit `.env`, API keys, client secrets, or other credentials to the repository.**

## Running the Application

### Start MCP Server

```bash
python -m mcp_server.server
```

### Start FastAPI

```bash
uvicorn app.api.main:app --reload
```

### Start Streamlit

```bash
streamlit run streamlit_app.py
```

Default local endpoints:

- Streamlit: `http://localhost:8501`
- FastAPI: `http://localhost:8000`
- MCP: `http://127.0.0.1:8001/mcp`

## Testing

Run the complete test suite:

```bash
pytest
```

Run Ruff:

```bash
ruff check mcp_server app tests streamlit_app.py
```

Both should pass before submission.

## Example Questions

### Knowledge Search

```text
What caused the payment gateway failure?
```

### Research

```text
What recurring factors caused payment incidents in 2025?
```

### Follow-up

```text
What payment incidents happened in 2025?
Which was the most recent?
What was its root cause?
```

### Structured Analysis

```text
How many payment incidents occurred in 2025?
```

### Out of Scope

```text
What is the capital of Sri Lanka?
```

This should be identified as outside the enterprise knowledge-base scope rather than answered using external knowledge.

## Spec-Driven Development

The project uses version-controlled specifications to drive incremental implementation.

Each feature increment follows:

```text
Specification
     ↓
Acceptance Criteria
     ↓
Implementation
     ↓
Automated Tests
     ↓
Validation
```

Current specifications:

- `specs/001-foundation.md` — original system requirements and acceptance criteria.
- `specs/002-production-hardening.md` — security, rate limiting, validation, timeout, and failure-handling increments.
- `specs/003-research-and-analysis.md` — research, MCP, contextual follow-up, structured analysis, evidence aggregation, and citation behavior.

The specifications are kept alongside the implementation so design intent and delivered behavior can be reviewed together.

## Current Status

The core enterprise assistant workflow is implemented and covered by automated tests and linting.

The application currently supports authenticated enterprise users, role-based document access, hybrid document retrieval, research workflows, MCP integration, contextual follow-up questions, citation validation, streaming responses, persistent conversations, per-user rate limiting, dependency failure handling, structured analysis, LangSmith observability, and automated testing/linting.
