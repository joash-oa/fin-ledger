from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuthSession


class AuthSessionDao:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_auth_session(
        self, session_token_hash: str, user_id: UUID
    ) -> AuthSession: ...

    async def get_auth_session_by_hash(
        self, session_token_hash: str
    ) -> AuthSession | None: ...

    async def update_last_activity(
        self, session_token_hash: str, timestamp: datetime
    ) -> None: ...

    async def delete_auth_session(self, session_token_hash: str) -> None: ...
