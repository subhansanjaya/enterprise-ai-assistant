# Enterprise AI Assistant

An enterprise-focused AI assistant for authenticated users to search and investigate information from an organization's internal knowledge base.

The application combines hybrid Retrieval-Augmented Generation (RAG), role-based access control, LangGraph-based agent orchestration, conversational context, citation validation, and streaming responses.

## Key Features

- **Enterprise Knowledge Search** — semantic search with embeddings and Pinecone, BM25 keyword retrieval, and hybrid ranking.
- **Role-Based Access Control** — Keycloak authentication, JWT validation, and retrieval-time document access filtering.
- **Multi-Agent Workflow** — supervisor routing, knowledge search, research, research evaluation, and iterative follow-up searches.
- **Conversational Context** — PostgreSQL conversation persistence and contextualized follow-up questions.
- **Citations** — answers cite supporting enterprise documents using document IDs, with citation validation.
- **Streaming** — responses can be streamed incrementally to the Streamlit interface.
- **Out-of-Scope Handling** — unrelated requests are identified and rejected rather than answered using external knowledge.

## Architecture

```text
                         ┌──────────────────────┐
                         │      Streamlit       │
                         │         UI           │
                         └──────────┬───────────┘
                                    │ HTTP / SSE
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │      REST API        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      Keycloak        │
                         │ Authentication/RBAC  │
                         └──────────────────────┘

                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      LangGraph       │
                         │   Agent Workflow     │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
          │ Supervisor  │    │   Context   │    │  Response   │
          └──────┬──────┘    └─────────────┘    └─────────────┘
                 │
          ┌──────┴──────────────┐
          ▼                     ▼
   ┌─────────────┐       ┌─────────────┐
   │  Retrieval  │       │   Research  │
   └──────┬──────┘       └──────┬──────┘
          │                     │
          └──────────┬──────────┘
                     ▼
          ┌──────────────────────────────┐
          │           RAG Layer          │
          │ Pinecone + BM25 + Hybrid    │
          └──────────────────────────────┘

                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │ Conversations   │
                    │   & Messages    │
                    └─────────────────┘
```

## Agent Workflow

### Knowledge Search

```text
User question → Supervisor → Query Contextualization → Hybrid Retrieval
→ Response Generation → Citation Validation → Answer
```

### Research

```text
User question → Supervisor → Query Contextualization → Research Agent
→ Document Search → Research Evaluator
                         │
              More evidence required ──→ Research Agent
                         │
                 Sufficient evidence
                         ↓
                      Response
```

Research is limited to a configured maximum number of iterations to avoid unnecessary repeated searches.

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

The highest-ranked documents are supplied to the response workflow.

## Conversation Context

Conversation messages are persisted in PostgreSQL. The supervisor determines whether a question depends on previous conversation context.

For example:

```text
User: What payment incidents happened in 2025?
Assistant: ... INC-2025-001 ... INC-2025-017
User: Which was the most recent?
```

The contextualization agent can transform the follow-up into a self-contained query such as:

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

### Authentication

- Keycloak
- OpenID Connect
- JWT

### Frontend

- Streamlit

### Research / Integration

- MCP

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
│   │   └── routes/
│   ├── auth/
│   ├── db/
│   ├── rag/
│   └── mcp/
├── data/
├── tests/
├── streamlit_app.py
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

Configure the required environment variables for OpenAI, Pinecone, PostgreSQL, and Keycloak according to the application's configuration.

Do not commit secrets or credentials to the repository.

## Running the Application

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

## Testing

Run the complete test suite:

```bash
pytest
```

Run Ruff:

```bash
ruff check app tests streamlit_app.py
```

## Example Questions

### Knowledge Search

```text
What caused the payment gateway failure?
```

```text
What is the payment API architecture?
```

### Research

```text
What recurring factors caused payment incidents in 2025?
```

```text
Compare the payment incidents and identify common causes.
```

### Follow-up

```text
What payment incidents happened in 2025?
Which was the most recent?
What was its root cause?
```

### Out of Scope

```text
What is the capital of France?
```

This should be identified as outside the enterprise knowledge-base scope rather than answered using external knowledge.

## Design Considerations

The application separates routing, contextualization, retrieval, research, and response generation so each responsibility can be independently tested and extended.

Security is enforced at the retrieval layer rather than relying solely on the response model to avoid exposing unauthorized documents.

Hybrid retrieval combines semantic understanding with exact keyword matching, which is particularly useful for enterprise documents containing identifiers and technical terminology.

## Current Status

The core enterprise assistant workflow is implemented and covered by automated tests. The application currently supports authenticated enterprise users, role-based document access, hybrid document retrieval, research workflows, contextual follow-up questions, citation validation, streaming responses, persistent conversations, and automated testing/linting.
