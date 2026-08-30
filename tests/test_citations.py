from app.agents.citations import (
    extract_citations,
    validate_citations,
)


def test_extract_citations() -> None:
    answer = (
        "The incident was caused by database exhaustion "
        "[INC-2025-001]. A second incident occurred later "
        "[INC-2025-017]."
    )

    assert extract_citations(answer) == [
        "INC-2025-001",
        "INC-2025-017",
    ]


def test_extract_citations_removes_duplicates() -> None:
    answer = (
        "The incident [INC-2025-001] was related to "
        "the same issue [INC-2025-001]."
    )

    assert extract_citations(answer) == [
        "INC-2025-001",
    ]


def test_validate_citations_accepts_valid_citations() -> None:
    answer = (
        "Database exhaustion caused the incident "
        "[INC-2025-001]."
    )

    invalid = validate_citations(
        answer,
        {"INC-2025-001"},
    )

    assert invalid == []


def test_validate_citations_rejects_unknown_citations() -> None:
    answer = (
        "The incident was caused by database exhaustion "
        "[INC-999-999]."
    )

    invalid = validate_citations(
        answer,
        {"INC-2025-001", "INC-2025-017"},
    )

    assert invalid == [
        "INC-999-999",
    ]


def test_validate_citations_detects_mixed_citations() -> None:
    answer = (
        "The incidents were related [INC-2025-001] "
        "and [INC-999-999]."
    )

    invalid = validate_citations(
        answer,
        {"INC-2025-001"},
    )

    assert invalid == [
        "INC-999-999",
    ]
