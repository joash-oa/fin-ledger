import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import (
    DuplicateEmailException,
    InvalidCredentialsException,
    InvalidSessionException,
)
from app.core.utils import (
    get_password_hash,
    get_token_hash,
    verify_password,
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
settings = get_settings()


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

    async def _create_session_token(self, user_id: UUID) -> SessionToken:
        session_token = secrets.token_urlsafe(32)
        session_token_hash = get_token_hash(session_token)
        await self.auth_session_dao.create_auth_session(
            user_id=user_id,
            session_token_hash=session_token_hash,
        )

        return SessionToken(
            value=session_token, max_age=settings.session_max_lifetime_seconds
        )

    async def register(
        self, first_name: str, last_name: str, email: str, password: str
    ) -> AuthResult:
        existing = await self.user_dao.get_user_by_email(email)
        if existing:
            raise DuplicateEmailException

        password_hash = get_password_hash(password)
        user = await self.user_dao.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
        )

        session_token = await self._create_session_token(user.id)
        return AuthResult(user_id=user.id, session_token=session_token)

    async def login(self, email: str, password: str) -> AuthResult:
        user = await self.user_dao.get_user_by_email(email)
        if not user:
            verify_password(
                password, DUMMY_PASSWORD_HASH
            )  # run verify against dummy password so timing is the same
            raise InvalidCredentialsException

        password_match = verify_password(password, user.password_hash)
        if not password_match:
            raise InvalidCredentialsException

        session_token = await self._create_session_token(user.id)
        return AuthResult(user_id=user.id, session_token=session_token)

    async def authenticate(self, session_token: str) -> AuthenticatedUser:
        session_token_hash = get_token_hash(session_token)
        auth_session = await self.auth_session_dao.get_auth_session_by_hash(
            session_token_hash
        )
        if not auth_session:
            raise InvalidSessionException

        now = self.now()
        idle_timeout_seconds = timedelta(seconds=settings.session_idle_timeout_seconds)
        if (now - auth_session.last_activity_at) >= idle_timeout_seconds:
            raise InvalidSessionException

        max_lifetime_seconds = timedelta(seconds=settings.session_max_lifetime_seconds)
        if (now - auth_session.created_at) >= max_lifetime_seconds:
            raise InvalidSessionException

        await self.auth_session_dao.update_last_activity(
            session_token_hash=session_token_hash, timestamp=now
        )

        return AuthenticatedUser(user_id=auth_session.user_id)

    async def logout(self, session_token: str) -> None:
        session_token_hash = get_token_hash(session_token)
        await self.auth_session_dao.delete_auth_session(session_token_hash)
