from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.utils import (
    get_password_hash,
    verify_password,  # noqa
)
from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao


@dataclass
class AuthenticatedUser:
    user_id: UUID


@dataclass
class SessionToken:
    value: str
    max_age: int


@dataclass
class AuthResult:
    user_id: UUID
    session_token: SessionToken


DUMMY_PASSWORD_HASH = get_password_hash("DUMMY_PASSWORD")


class AuthService:
    def __init__(
        self,
        user_dao: UserDao,
        auth_session_dao: AuthSessionDao,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self.user_dao = user_dao
        self.auth_session_dao = auth_session_dao
        self.now = now

    async def register(
        self, first_name: str, last_name: str, email: str, password: str
    ) -> AuthResult: ...

    async def login(self, email: str, password: str) -> AuthResult: ...

    async def authenticate(self, session_token: str) -> AuthenticatedUser: ...

    async def logout(self, session_token: str) -> None: ...
