from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: str
    roles: list[str]

    @property
    def primary_role(self) -> str:
        return self.roles[0] if self.roles else "viewer"