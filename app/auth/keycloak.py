from jose import jwt
import httpx

from app.auth.models import AuthenticatedUser
from app.config import settings


class KeycloakAuthenticationService:
    def __init__(self) -> None:
        self._issuer = (
            f"{settings.keycloak_url}"
            f"/realms/{settings.keycloak_realm}"
        )

        self._jwks_url = (
            f"{self._issuer}"
            "/protocol/openid-connect/certs"
        )

    async def authenticate(
        self,
        token: str,
    ) -> AuthenticatedUser:
        async with httpx.AsyncClient() as client:
            response = await client.get(self._jwks_url)
            response.raise_for_status()

            jwks = response.json()

        unverified_header = jwt.get_unverified_header(token)

        key = next(
            (
                key
                for key in jwks["keys"]
                if key["kid"] == unverified_header["kid"]
            ),
            None,
        )

        if key is None:
            raise ValueError("Unable to find signing key.")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=self._issuer,
            options={
                "verify_aud": False,
            },
        )

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Token does not contain a subject.")

        roles = payload.get(
            "realm_access",
            {},
        ).get(
            "roles",
            [],
        )

        return AuthenticatedUser(
            user_id=user_id,
            roles=roles,
        )