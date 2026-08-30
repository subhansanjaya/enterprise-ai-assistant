# 002 — Production Hardening

## Purpose

Define the hardening increment added after the foundation implementation.

## Scope

- Per-user token-bucket rate limiting
- Input validation
- MCP validation
- MCP timeout handling
- Dependency failure handling
- Controlled application errors
- Citation validation
- Authorization enforcement

## Requirements

### REQ-002-001 — Rate Limiting

The API shall enforce a configurable token-bucket rate limit per authenticated user.

### REQ-002-002 — Input Validation

Invalid request and tool parameters shall be rejected before unnecessary processing.

### REQ-002-003 — MCP Timeout

MCP calls shall have a configurable timeout and return controlled timeout errors.

### REQ-002-004 — Dependency Failure Handling

LLM, retrieval, MCP, and related dependency failures shall be handled without exposing raw internal exceptions.

### REQ-002-005 — Retrieval Authorization

Retrieved evidence shall be filtered according to the authenticated user's roles.

### REQ-002-006 — Citation Validation

Generated document citations shall reference only documents available in the response evidence.

## Acceptance Criteria

- Requests exceeding the configured per-user rate limit are rejected gracefully.
- Invalid roles and `top_k` values are rejected.
- Empty MCP search queries are rejected.
- MCP timeouts become controlled errors.
- MCP service failures become controlled errors.
- Unauthorized access levels are not returned through retrieval.
- Invalid document citations are rejected.
- External dependency failures do not expose raw stack traces to users.

## Verification

```bash
ruff check mcp_server app tests streamlit_app.py
pytest
```

## Completion

This increment is complete when the acceptance criteria are satisfied and the automated validation commands pass.
