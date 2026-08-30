from app.auth.policy import (
    build_access_filter,
    get_allowed_access_levels,
)


def test_viewer_can_access_internal() -> None:
    assert get_allowed_access_levels(
        ["viewer"]
    ) == {"internal"}


def test_analyst_can_access_internal_and_restricted() -> None:
    assert get_allowed_access_levels(
        ["analyst"]
    ) == {"internal", "restricted"}


def test_admin_can_access_all_levels() -> None:
    assert get_allowed_access_levels(
        ["admin"]
    ) == {
        "internal",
        "restricted",
        "confidential",
    }


def test_multiple_roles_combine_access() -> None:
    assert get_allowed_access_levels(
        ["viewer", "analyst"]
    ) == {
        "internal",
        "restricted",
    }


def test_unknown_role_has_no_access() -> None:
    assert get_allowed_access_levels(
        ["unknown"]
    ) == set()
    
def test_viewer_filter() -> None:
    assert build_access_filter(
        ["viewer"]
    ) == {
        "access_level": {
            "$in": ["internal"],
        }
    }


def test_analyst_filter() -> None:
    assert build_access_filter(
        ["analyst"]
    ) == {
        "access_level": {
            "$in": ["internal", "restricted"],
        }
    }


def test_admin_filter() -> None:
    assert build_access_filter(
        ["admin"]
    ) == {
        "access_level": {
            "$in": [
                "confidential",
                "internal",
                "restricted",
            ],
        }
    }


def test_unknown_role_has_empty_filter() -> None:
    assert build_access_filter(
        ["unknown"]
    ) == {
        "access_level": {
            "$in": [],
        }
    }