from dataclasses import dataclass
from uuid import UUID

from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao


@dataclass
class AuthenticatedUser:
    user_id: UUID
    first_name: str
    last_name: str
    email: str


@dataclass
class SessionToken:
    value: str
    max_age: int


@dataclass
class AuthResult:
    user_id: UUID
    session_token: SessionToken


class AuthService:
    def __init__(self, user_dao: UserDao, auth_session_dao: AuthSessionDao):
        self.user_dao = user_dao
        self.auth_session_dao = auth_session_dao

    async def register(
        self, first_name: str, last_name: str, email: str, password: str
    ) -> AuthResult: ...

    async def login(self, email: str, password: str) -> AuthResult: ...

    async def logout(self, session_token: str) -> None: ...

    async def authenticate(self, token: str) -> AuthenticatedUser: ...
