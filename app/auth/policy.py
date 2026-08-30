from typing import Final

ROLE_ACCESS_LEVELS: Final[dict[str, set[str]]] = {
    "viewer": {"internal"},
    "analyst": {"internal", "restricted"},
    "admin": {"internal", "restricted", "confidential"},
}


def get_allowed_access_levels(
    roles: list[str],
) -> set[str]:
    allowed_levels: set[str] = set()

    for role in roles:
        allowed_levels.update(
            ROLE_ACCESS_LEVELS.get(role, set())
        )

    return allowed_levels


def build_access_filter(
    roles: list[str],
) -> dict:
    allowed_levels = get_allowed_access_levels(roles)

    if not allowed_levels:
        return {
            "access_level": {
                "$in": []
            }
        }

    return {
        "access_level": {
            "$in": sorted(allowed_levels)
        }
    }