# Enterprise AI Assistant — Architecture

## 1. Architecture Overview

The system is designed as a modular AI application consisting of:

* Streamlit presentation layer
* FastAPI application/API layer
* LangGraph agent orchestration layer
* Retrieval and RAG layer
* Enterprise tool layer
* Security and authorization layer
* Conversational memory
* Observability through LangSmith

The architecture intentionally separates application concerns from AI orchestration, retrieval, tools and security.

---

## 2. High-Level Architecture

```text
                           ┌──────────────────────┐
                           │        User          │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │      Streamlit       │
                           │                      │
                           │ Chat Interface       │
                           │ Agent Activity       │
                           │ Streaming Responses  │
                           └──────────┬───────────┘
                                      │
                                      │ HTTP
                                      ▼
                           ┌──────────────────────┐
                           │       FastAPI        │
                           │                      │
                           │ Authentication       │
                           │ Request Validation   │
                           │ Rate Limiting        │
                           │ Error Handling       │
                           └──────────┬───────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────┐
                  │             LangGraph              │
                  │                                    │
                  │          Supervisor Agent          │
                  │                 │                  │
                  │          ┌──────┴──────┐           │
                  │          ▼             ▼           │
                  │     Retrieval       Research      │
                  │       Agent           Agent        │
                  │          │             │            │
                  │          └──────┬──────┘            │
                  │                 ▼                  │
                  │          Response Agent            │
                  └─────────────────┬──────────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
           ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
           │  Pinecone   │  │ MCP Server  │  │   Python    │
           │             │  │             │  │   Analysis  │
           │ Hybrid RAG  │  │ Enterprise  │  │    Tool     │
           │             │  │ Data        │  │             │
           └─────────────┘  └─────────────┘  └─────────────┘


        ┌───────────────────────────────────────────────┐
        │              Cross-Cutting Services           │
        │                                               │
        │ Security │ RBAC │ Guardrails │ Memory        │
        │ Structured Logging │ LangSmith Observability │
        └───────────────────────────────────────────────┘
```

---

## 3. Request Flow

A typical request follows this flow:

```text
User
  │
  ▼
Streamlit
  │
  ▼
FastAPI
  │
  ├── Authenticate user
  │
  ├── Validate request
  │
  ├── Apply rate limit
  │
  ▼
LangGraph
  │
  ▼
Supervisor
  │
  ├───────────────┐
  ▼               ▼
Retrieval       Research
  │               │
  │               ├── Search
  │               ├── Decompose
  │               ├── Analyze
  │               └── Aggregate
  │               │
  └───────┬───────┘
          ▼
   Response Agent
          │
          ▼
   Citation Validation
          │
          ▼
      Final Answer
          │
          ▼
      Streamlit
```

---

## 4. Presentation Layer

### Streamlit

Streamlit provides the lightweight user interface.

Responsibilities:

* Display conversation history.
* Accept user messages.
* Display streaming responses.
* Display agent activity.
* Display retrieval status.
* Display tool execution status.
* Display validation status.
* Display citations.

The frontend intentionally prioritizes transparency and functionality over visual design.

---

## 5. API Layer

### FastAPI

FastAPI acts as the application boundary between the frontend and the AI orchestration system.

Responsibilities:

* Expose asynchronous API endpoints.
* Authenticate users.
* Validate incoming requests.
* Apply rate limiting.
* Invoke the LangGraph workflow.
* Handle application exceptions.
* Return structured responses/events.

The API layer should not contain agent-specific reasoning logic.

---

## 6. Agent Orchestration Layer

### LangGraph

LangGraph is responsible for orchestrating the specialized agents.

The initial graph contains:

```text
Supervisor
    │
    ├── Retrieval Agent
    │
    ├── Research Agent
    │
    └── Response Agent
```

### Supervisor

The Supervisor:

1. Understands the user's intent.
2. Determines the required workflow.
3. Routes requests to specialized agents.
4. Controls unnecessary tool execution.

### Retrieval Agent

The Retrieval Agent:

1. Creates or receives a retrieval query.
2. Searches the organizational knowledge base.
3. Applies metadata filters.
4. Enforces access constraints.
5. Returns ranked evidence.

### Research Agent

The Research Agent handles complex questions.

It can:

1. Create a research plan.
2. Decompose a large question.
3. Retrieve targeted document groups.
4. Analyze groups independently.
5. Repeat retrieval when required.
6. Aggregate findings.

This provides the simplified RLM behavior required by the assessment.

### Response Agent

The Response Agent:

1. Receives relevant evidence.
2. Uses conversation context.
3. Produces the final answer.
4. Includes supporting citations.
5. Avoids unsupported claims.

---

## 7. Shared Agent State

Agents communicate through explicit LangGraph state.

Conceptually:

```text
AgentState

├── messages
├── user_id
├── user_role
├── intent
├── retrieved_documents
├── research_results
├── tool_calls
├── validation_results
└── final_answer
```

Typed state will be preferred to make agent transitions explicit and easier to test.

---

## 8. Retrieval Architecture

The retrieval system uses hybrid search.

```text
                    User Query
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       Dense Retrieval      Sparse Retrieval
              │                   │
              │                   │
              └─────────┬─────────┘
                        ▼
                 Hybrid Ranking
                        │
                        ▼
                Access Filtering
                        │
                        ▼
                  Top Evidence
```

### Dense Retrieval

Embedding-based semantic retrieval.

Useful when the query expresses a concept differently from the wording in the documents.

### Sparse Retrieval

Keyword-based retrieval.

Useful for:

* Error codes
* Incident identifiers
* Service names
* Product names
* Exact terminology

### Hybrid Ranking

Dense and sparse scores are combined to produce a final ranking.

The exact weighting will be configurable and documented as an implementation decision.

---

## 9. Pinecone

Pinecone provides the vector database for the knowledge retrieval layer.

Documents will be represented as chunks with associated metadata.

Example:

```json
{
  "document_id": "INC-2025-001",
  "document_type": "incident",
  "department": "payments",
  "access_level": "internal",
  "created_date": "2025-01-01"
}
```

Metadata filtering will be used to prevent retrieval of documents outside the user's permitted scope.

Namespaces may be used to logically isolate document collections where appropriate.

---

## 10. Document Ingestion

The ingestion pipeline will initially operate on mock enterprise documents.

```text
Documents
    │
    ▼
Document Loader
    │
    ▼
Text Extraction
    │
    ▼
Chunking
    │
    ▼
Metadata Enrichment
    │
    ▼
Embeddings
    │
    ▼
Pinecone
```

Initial document categories:

* Incident reports
* Architecture documents
* Operational runbooks
* Product specifications

---

## 11. RLM Architecture

The Research Agent implements a simplified recursive/decomposed research workflow.

```text
                 Complex Question
                        │
                        ▼
                 Research Planner
                        │
                        ▼
                 Search Plan
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Batch 1       Batch 2       Batch 3
          │             │             │
          ▼             ▼             ▼
       Analyze        Analyze        Analyze
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  Aggregation
                        │
                        ▼
                  Response Agent
```

The objective is to avoid placing an entire document collection into a single LLM context.

Instead, the system performs targeted exploration, analysis and aggregation.

---

## 12. Tool Architecture

The system exposes narrowly scoped tools.

### Knowledge Search

```text
Agent
  │
  ▼
Knowledge Search Tool
  │
  ▼
Hybrid Retrieval
```

### Python Analysis

```text
Agent
  │
  ▼
Python Analysis Tool
  │
  ▼
Deterministic Analysis
```

This tool is intended for structured calculations rather than asking the LLM to perform complex numerical analysis itself.

### MCP

```text
LangGraph
    │
    ▼
MCP Client
    │
    ▼
MCP Server
    │
    ├── Employee Directory
    ├── Service Catalog
    └── Incident Records
```

The MCP server provides dummy enterprise data for the proof of concept.

---

## 13. Security Architecture

Security is implemented as a separate concern rather than delegated to the LLM.

```text
User Request
     │
     ▼
Authentication
     │
     ▼
RBAC
     │
     ▼
Input Validation
     │
     ▼
Prompt Injection Protection
     │
     ▼
LangGraph
     │
     ▼
Tool Authorization
     │
     ▼
Tool Execution
```

### Important Security Principle

The LLM may request a tool, but it cannot authorize itself to execute that tool.

Authorization is enforced by application code.

---

## 14. Role-Based Access Control

The initial implementation uses three roles:

```text
Viewer
Analyst
Administrator
```

Conceptually:

```text
                 ┌───────────┐
                 │   User    │
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │    RBAC   │
                 └─────┬─────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Viewer       Analyst    Administrator
```

Permissions are checked before executing protected tools.

---

## 15. Prompt Injection Protection

Retrieved documents are treated as untrusted content.

The system should distinguish between:

```text
System Instructions
       ≠
User Input
       ≠
Retrieved Content
       ≠
Tool Output
```

Instructions found inside retrieved documents must not automatically become agent instructions.

Security checks should address:

* Instruction override attempts
* Data exfiltration attempts
* Tool abuse
* Malicious tool parameters

---

## 16. Memory

Conversation memory is initially session-based.

```text
User
 │
 ▼
Conversation
 │
 ├── Previous Questions
 ├── Previous Answers
 └── Relevant Context
 │
 ▼
Current Agent Request
```

This provides multi-turn conversational context without introducing unnecessary persistent infrastructure for the POC.

---

## 17. Observability

LangSmith provides distributed tracing across the AI workflow.

A typical trace should represent:

```text
Conversation
    │
    ▼
Supervisor
    │
    ├── Retrieval Agent
    │      └── Pinecone Search
    │
    ├── Research Agent
    │      ├── Search
    │      ├── Analysis
    │      └── Aggregation
    │
    └── Response Agent
```

The system should record:

* Conversation execution
* Agent transitions
* Tool calls
* Retrieval operations
* Important validation operations

The Streamlit interface will provide a simplified human-readable representation of this execution.

---

## 18. Rate Limiting

A token bucket is used at the API boundary.

```text
Request
   │
   ▼
Token Bucket
   │
   ├── Token available → Continue
   │
   └── No token → Reject gracefully
```

Limits are configured per user.

---

## 19. Error Handling

External dependencies are treated as failure boundaries.

Examples:

```text
LLM Failure
    ↓
Controlled error response

Pinecone Failure
    ↓
Retrieval error / graceful degradation

MCP Failure
    ↓
Tool failure / informative response

Tool Timeout
    ↓
Timeout handling

Invalid Request
    ↓
Validation error

Unauthorized Tool
    ↓
Authorization rejection
```

The application should avoid exposing internal exceptions directly to users.

---

## 20. Observability and Transparency in the UI

The Streamlit activity panel provides a simplified execution timeline.

Example:

```text
✓ Request received

✓ User authenticated
✓ Request validated

→ Supervisor
  Intent: knowledge_search

→ Retrieval Agent
  Hybrid search started

→ Pinecone
  8 candidates retrieved

✓ Access filtering completed

→ Response Agent
  Generating answer

✓ Citation validation completed

✓ Response delivered
```

This is intentionally a user-facing representation rather than exposing raw internal reasoning or hidden chain-of-thought.

---

## 21. Deployment

For the proof of concept, the application should be runnable locally.

The target deployment structure is:

```text
┌───────────────────────────────────────┐
│            Local Environment          │
│                                       │
│  Streamlit                            │
│      │                                │
│      ▼                                │
│  FastAPI                              │
│      │                                │
│      ▼                                │
│  LangGraph                            │
│      │                                │
│  ┌───┼───────────┐                    │
│  ▼   ▼           ▼                    │
│ Pinecone MCP   Python Tool             │
│                                       │
└───────────────────────────────────────┘

External Services:

Pinecone
LangSmith
LLM Provider
```

Containerization may be added later if time permits.

---

## 22. Key Design Decisions

### Decision 1 — LangGraph

Chosen because the assessment explicitly requires LangGraph and multiple specialized agents.

### Decision 2 — FastAPI

Provides a clean asynchronous API boundary between the UI and AI orchestration.

### Decision 3 — Pinecone

Chosen because the assessment explicitly requires Pinecone and hybrid retrieval.

### Decision 4 — Session Memory

Chosen for the POC because it demonstrates conversational memory without introducing unnecessary persistence infrastructure.

### Decision 5 — Hardcoded Authentication

Chosen because the assessment explicitly permits hardcoded users and roles.

### Decision 6 — Simplified RLM

Chosen because the assessment permits a simplified RLM implementation while requiring the concept to be demonstrated.

### Decision 7 — Mock Enterprise Data

Chosen because the assessment explicitly permits generated mock data.

### Decision 8 — Application-Level Authorization

Authorization is intentionally kept outside the LLM to ensure the agent cannot bypass role restrictions.

---

## 23. Architectural Principles

1. Separate presentation, API, orchestration, retrieval and infrastructure concerns.
2. Keep authorization outside the LLM.
3. Treat retrieved content as untrusted.
4. Keep tools narrowly scoped.
5. Use explicit typed agent state.
6. Make agent execution observable.
7. Prefer deterministic computation for structured analysis.
8. Fail gracefully at external dependency boundaries.
9. Keep the POC simple enough to explain and demonstrate.
10. Optimize for demonstrable enterprise architecture rather than unnecessary infrastructure complexity.
