# Enterprise AI Assistant — Architecture

## 1. Overview

The system is a modular enterprise AI application composed of:

- Streamlit presentation
- FastAPI API
- LangGraph agent orchestration
- Hybrid RAG
- MCP tool integration
- Keycloak authentication and RBAC
- PostgreSQL conversation persistence
- Per-user rate limiting
- Dependency failure handling
- Citation validation
- LangSmith observability

The architecture separates presentation, API, orchestration, retrieval, tools, security, persistence, and infrastructure concerns.

## 2. High-Level Architecture

```text
                           ┌──────────────────────┐
                           │        User          │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │      Streamlit       │
                           │ Chat / Activity UI   │
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
                   ┌──────────────────┼──────────────────┐
                   ▼                  ▼                  ▼
             Context Agent      Retrieval Agent    Research Agent
                   │                  │                  │
                   │                  ▼                  ▼
                   │             Hybrid RAG          MCP Client
                   │                  │                  │
                   └──────────────────┴──────────────────┘
                                      │
                                      ▼
                               Response Agent
                                      │
                                      ▼
                               Citation Validation
                                      │
                                      ▼
                                  Final Answer

        ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
        │   Pinecone     │  │  PostgreSQL    │  │  LangSmith     │
        │ Vector Search  │  │ Conversations  │  │  Tracing       │
        └────────────────┘  └────────────────┘  └────────────────┘

                              ┌────────────────┐
                              │   MCP Server   │
                              │ Search +       │
                              │ Analysis Tools │
                              └────────────────┘
```

## 3. Request Flow

```text
User
  │
  ▼
Streamlit
  │
  ▼
FastAPI
  │
  ├── Authenticate
  ├── Validate
  ├── Rate limit
  │
  ▼
Supervisor
  │
  ├── general ────────────────► Response
  │
  ├── out_of_scope ──────────► Response
  │
  ├── knowledge_search
  │       │
  │       ▼
  │   Contextualization
  │       │
  │       ▼
  │   Retrieval
  │       │
  │       ▼
  │   Response
  │
  └── research
          │
          ▼
      Contextualization
          │
          ▼
      Research Agent
          │
          ├── MCP Search
          │
          ├── Structured Analysis
          │
          ▼
      Research Evaluator
          │
          ├── insufficient → follow-up search
          │
          └── sufficient → Response
```

## 4. Presentation Layer

Streamlit provides the user interface.

Responsibilities:

- conversation display
- message input
- streaming response display
- activity/status display
- citations and source information

The frontend does not enforce enterprise authorization; authorization remains a backend concern.

## 5. API Layer

FastAPI is the application boundary.

Responsibilities:

- authentication dependencies
- request validation
- per-user rate limiting
- conversation loading/persistence
- LangGraph invocation
- streaming response delivery
- controlled HTTP errors

The API layer does not contain agent reasoning logic.

## 6. LangGraph Layer

### Supervisor

The supervisor classifies requests into:

- `general`
- `knowledge_search`
- `research`
- `out_of_scope`

It also determines whether the latest question depends on previous conversation context.

### Contextualization

Contextualization converts dependent follow-up questions into self-contained enterprise queries.

Example:

```text
Previous:
What payment incidents happened in 2025?

Follow-up:
Which was the most recent?

Rewritten:
What was the most recent payment incident reported in 2025?
```

### Retrieval Agent

The retrieval agent:

1. obtains the contextualized query
2. calls the retrieval service
3. applies role-based filtering
4. returns ranked evidence

### Research Agent

The research agent:

1. contextualizes the research question
2. searches enterprise evidence through MCP
3. tracks retrieved chunks
4. avoids counting duplicate chunks as new evidence
5. optionally invokes structured analysis
6. maintains research iteration state

### Research Evaluator

The evaluator decides whether evidence is sufficient.

If not sufficient, it can produce one focused follow-up query.

Research is bounded by `MAX_RESEARCH_ITERATIONS`.

### Response Agent

The response agent generates the final answer from supplied evidence and validates citations for knowledge-search and research responses.

## 7. Shared Agent State

The shared state contains:

```text
messages
user_id
user_roles
contextualized_query
requires_context
research_query
research_new_documents
research_evaluation
intent
retrieved_documents
research_results
research_queries
research_iteration
final_answer
analysis_result
```

Explicit state keeps agent transitions testable.

## 8. Retrieval Architecture

```text
                     User Query
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       Dense Retrieval       Sparse Retrieval
              │                     │
              │                     │
              └──────────┬──────────┘
                         ▼
                  Hybrid Ranking
                         │
                         ▼
                  Access Filtering
                         │
                         ▼
                    Top Evidence
```

Dense retrieval provides semantic matching. BM25 provides lexical matching for exact enterprise terms and identifiers.

The hybrid ranker normalizes the two score sets and combines them using configured weights.

## 9. Authorization

Authentication uses Keycloak/OpenID Connect.

Initial role mapping:

```text
viewer
  └── internal

analyst
  ├── internal
  └── restricted

admin
  ├── internal
  ├── restricted
  └── confidential
```

The authenticated user's roles are passed into retrieval/tool operations.

Authorization is enforced by application code and retrieval filters, not by the LLM.

## 10. MCP Architecture

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

### `search_documents`

Validates:

- query
- roles
- role membership
- `top_k`

Then applies the role-derived access filter before searching the enterprise knowledge base.

### `analyze_documents`

Provides constrained structured analysis:

```text
count
group_by
percentage
latest
earliest
```

The analysis input consists of already retrieved documents.

Arbitrary Python code execution is intentionally not exposed.

## 11. Structured Analysis

The analysis tool is intended for deterministic calculations over structured retrieved data.

Examples:

```text
How many incidents are there?
What percentage of records belong to each type?
Which record is the latest?
Which record is the earliest?
```

This avoids relying on the LLM to perform basic arithmetic or date selection when deterministic computation is more reliable.

## 12. Research / RLM Workflow

```text
Complex Question
      │
      ▼
Contextualization
      │
      ▼
Research Agent
      │
      ▼
MCP Search
      │
      ▼
Structured Analysis when appropriate
      │
      ▼
Research Evaluator
      │
      ├── insufficient → focused follow-up search
      │
      └── sufficient → Response
```

Research terminates when sufficient evidence is available, no new evidence is found, the iteration limit is reached, or no valid follow-up query exists.

## 13. Conversation Persistence

PostgreSQL stores:

```text
Conversation
 ├── id
 ├── user_id
 ├── title
 ├── created_at
 └── updated_at

Message
 ├── id
 ├── conversation_id
 ├── role
 ├── content
 └── created_at
```

Conversation lookup is scoped to the authenticated user's ID.

## 14. Streaming

```text
FastAPI
   │
   ▼
Preparation Graph
   │
   ▼
Response Agent
   │
   ▼
LLM Streaming
   │
   ▼
SSE token events
   │
   ▼
Streamlit
```

The completed response is persisted after streaming completes.

## 15. Rate Limiting

A per-user token bucket protects the API.

```text
Request
   │
   ▼
Authenticated User
   │
   ▼
Token Bucket
   │
   ├── available → continue
   │
   └── exhausted → reject
```

This limits abuse while keeping the rate-limit scope aligned with authenticated users.

## 16. Failure Handling

External dependencies are treated as explicit failure boundaries.

```text
OpenAI
  ↓
timeout / exception handling

MCP
  ↓
timeout / exception handling

Pinecone
  ↓
retrieval failure handling

Validation
  ↓
controlled request errors

Authorization
  ↓
controlled access rejection
```

The application converts dependency failures into controlled errors and avoids exposing raw internal exceptions to users.

## 17. Citation Integrity

The response workflow requires document citations for knowledge-based answers.

A citation is valid only when the referenced document ID is available in the response state's retrieved evidence.

This provides a basic defense against unsupported source references.

## 18. Observability

LangSmith tracing can capture the major AI workflow stages:

```text
Supervisor
  ↓
Contextualization
  ↓
Retrieval / Research
  ↓
MCP
  ↓
Analysis
  ↓
Response
  ↓
Citation Validation
```

Streamlit presents simplified activity information without exposing chain-of-thought.

## 19. Security Principles

1. Authenticate before protected operations.
2. Authorize through application code.
3. Filter enterprise retrieval by role.
4. Treat retrieved content as untrusted data.
5. Keep MCP tools narrowly scoped.
6. Validate tool inputs.
7. Limit autonomous research iterations.
8. Avoid arbitrary code execution.
9. Do not expose credentials in source control.
10. Avoid returning raw internal exceptions to users.

## 20. Deployment

The current implementation is optimized for local proof-of-concept execution.

```text
Streamlit
    │
    ▼
FastAPI
    │
    ▼
LangGraph
    │
    ├── RAG → Pinecone
    ├── MCP → MCP Server
    └── Memory → PostgreSQL

External:
- OpenAI
- Keycloak
- Pinecone
- LangSmith
```

The components can later be containerized and deployed independently without changing the core application boundaries.

## 21. Architectural Principles

1. Separate presentation, API, orchestration, retrieval, tools, and infrastructure.
2. Keep authorization outside the LLM.
3. Treat retrieved content as untrusted.
4. Keep tools narrowly scoped.
5. Use explicit agent state.
6. Make execution observable.
7. Prefer deterministic analysis for structured calculations.
8. Fail gracefully at external dependency boundaries.
9. Bound autonomous research.
10. Keep specifications version controlled.
11. Validate implementation increments against acceptance criteria.
