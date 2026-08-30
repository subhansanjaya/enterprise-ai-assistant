# RAG Evaluation

This directory contains a small deterministic evaluation dataset for the
Enterprise AI Assistant retrieval system.

## Purpose

The automated tests under `tests/` verify that individual components and
application workflows behave correctly.

The evaluation suite in this directory focuses on retrieval quality against
representative enterprise questions with known relevant documents.

This provides a distinction between:

- Software correctness testing
- RAG retrieval evaluation
- Runtime observability through LangSmith

## Evaluation Method

Each evaluation case contains:

- A representative enterprise question
- The expected relevant document IDs

The evaluator executes the existing `RetrievalService` and calculates
Recall@5.

### Recall@5

Recall@5 is calculated as:

    relevant expected documents retrieved in top 5
    ------------------------------------------------
              total expected relevant documents

A score of 100% means all expected relevant documents were retrieved within
the top five results.

## Evaluation Dataset

The current dataset covers:

1. Payment incidents in 2025
2. The most recent payment incident
3. The cause of the May 2025 payment incident
4. Payment platform architecture
5. Payment gateway recovery procedures

## Running the Evaluation

From the project root:

```bash
pytest evals/test_retrieval_evaluation.py -s