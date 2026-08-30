# 003 — Research, Context, MCP and Structured Analysis

## Purpose

Define the incremental AI workflow capabilities added after the foundation and hardening increments.

## Scope

- Contextual follow-up resolution
- Research workflow
- Research evaluation
- Iterative evidence gathering
- MCP enterprise search
- Structured deterministic analysis
- Evidence aggregation
- Citation-aware findings

## Requirements

### REQ-003-001 — Contextual Follow-Ups

The system shall resolve context-dependent questions such as:

```text
Which was the most recent?
What was its root cause?
Were there any similar incidents?
```

### REQ-003-002 — Entity Preservation

Contextualization shall preserve important incident IDs, document IDs, dates, system names, and domain terminology when available.

### REQ-003-003 — Research Routing

Complex multi-document questions shall be routed to the research workflow.

### REQ-003-004 — Evidence Collection

The Research Agent shall collect enterprise evidence and retain source metadata.

### REQ-003-005 — Duplicate Avoidance

Repeated research searches shall not count an already retrieved chunk as new evidence.

### REQ-003-006 — Research Evaluation

The system shall evaluate whether collected evidence is sufficient and may issue one focused follow-up query when necessary.

### REQ-003-007 — Bounded Research

Research shall terminate when sufficient evidence is available, no new evidence is found, the maximum iteration count is reached, or no valid follow-up query exists.

### REQ-003-008 — MCP Integration

Research shall be able to search enterprise evidence through the MCP client/server boundary.

### REQ-003-009 — Structured Analysis

Structured questions shall support deterministic operations such as:

- count
- group_by
- percentage
- latest
- earliest

### REQ-003-010 — Evidence-Based Response

The response agent shall use supplied evidence only and shall state when evidence is insufficient.

### REQ-003-011 — Citation Integrity

Research findings and final responses shall use document IDs from available evidence.

## Acceptance Criteria

### AC-003-001 — Context

Given:

```text
What payment incidents happened in 2025?
Which was the most recent?
```

the second question shall be contextualized to payment incidents in 2025.

### AC-003-002 — Date Reasoning

Given:

```text
INC-2025-001 — 14 February 2025
INC-2025-017 — 22 May 2025
```

the system shall identify `INC-2025-017` as the most recent.

### AC-003-003 — Research

Complex questions shall trigger evidence collection and research evaluation.

### AC-003-004 — Research Termination

If no new evidence is discovered, the workflow shall stop rather than repeatedly searching the same evidence.

### AC-003-005 — Structured Analysis

The analysis tool shall perform deterministic operations over retrieved documents.

### AC-003-006 — Unsupported Claims

The response shall not invent facts absent from evidence.

### AC-003-007 — Citation Validation

Citations for unavailable document IDs shall be rejected.

## Verification

```bash
ruff check mcp_server app tests streamlit_app.py
pytest
```

Manual end-to-end verification:

```text
What payment incidents happened in 2025?
Which was the most recent?
```

Expected result: the system retrieves the relevant incidents and identifies the later incident with a valid citation.

## Completion

This increment is complete when the acceptance criteria are satisfied, automated tests pass, Ruff is clean, and the contextual follow-up scenario works end-to-end.
