from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuthSession


class AuthSessionDao:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_auth_session(
        self, session_token_hash: str, user_id: UUID
    ) -> AuthSession:
        auth_session = AuthSession(
            session_token_hash=session_token_hash, user_id=user_id
        )
        self.db_session.add(auth_session)
        await self.db_session.flush()

        return auth_session

    async def get_auth_session_by_hash(
        self, session_token_hash: str
    ) -> AuthSession | None:
        statement = select(AuthSession).where(
            AuthSession.session_token_hash == session_token_hash
        )
        result = await self.db_session.execute(statement)

        return result.scalar_one_or_none()

    async def update_last_activity(
        self, session_token_hash: str, timestamp: datetime
    ) -> None:
        statement = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .values(last_activity_at=timestamp)
        )
        await self.db_session.execute(statement)

    async def delete_auth_session(self, session_token_hash: str) -> None:
        statement = delete(AuthSession).where(
            AuthSession.session_token_hash == session_token_hash
        )
        await self.db_session.execute(statement)
