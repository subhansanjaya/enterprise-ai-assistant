from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.keycloak import KeycloakAuthenticationService
from app.auth.models import AuthenticatedUser

security = HTTPBearer()


def get_keycloak_service() -> KeycloakAuthenticationService:
    return KeycloakAuthenticationService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    auth_service: KeycloakAuthenticationService = Depends(
        get_keycloak_service
    ),
) -> AuthenticatedUser:
    try:
        return await auth_service.authenticate(
            credentials.credentials
        )
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials.",
        ) from exc