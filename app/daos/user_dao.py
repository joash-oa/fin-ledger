from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserDao:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
        self, first_name: str, last_name: str, email: str, password_hash: str
    ) -> User: ...

    async def get_user_by_email(self, email: str) -> User | None: ...

    async def get_user_by_id(self, user_id: UUID) -> User | None: ...
