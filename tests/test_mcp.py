from mcp_server.server import search_documents
import pytest


def test_mcp_viewer_only_gets_internal_documents() -> None:
    results = search_documents(
        query="payment database incident",
        roles=["viewer"],
        top_k=10,
    )

    assert results
    assert all(
        result["access_level"] == "internal"
        for result in results
    )


def test_mcp_analyst_can_access_restricted_documents() -> None:
    results = search_documents(
        query="confidential restricted payment information",
        roles=["analyst"],
        top_k=10,
    )

    assert all(
        result["access_level"] in {"internal", "restricted"}
        for result in results
    )


def test_mcp_admin_can_access_all_document_levels() -> None:
    results = search_documents(
        query="payment database incident",
        roles=["admin"],
        top_k=10,
    )

    assert results
    assert all(
        result["access_level"]
        in {"internal", "restricted", "confidential"}
        for result in results
    )


def test_mcp_rejects_empty_query() -> None:
    with pytest.raises(
        ValueError,
        match="Search query cannot be empty",
    ):
        search_documents(
            query="   ",
            roles=["viewer"],
        )


def test_mcp_rejects_missing_roles() -> None:
    with pytest.raises(
        ValueError,
        match="At least one role is required",
    ):
        search_documents(
            query="payment incident",
            roles=[],
        )


def test_mcp_rejects_unknown_role() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown role",
    ):
        search_documents(
            query="payment incident",
            roles=["superuser"],
        )


@pytest.mark.parametrize(
    "top_k",
    [0, -1, 11, 100],
)
def test_mcp_rejects_invalid_top_k(
    top_k: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="top_k must be between 1 and 10",
    ):
        search_documents(
            query="payment incident",
            roles=["viewer"],
            top_k=top_k,
        )