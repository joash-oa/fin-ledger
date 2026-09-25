from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserDao:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
        self, first_name: str, last_name: str, email: str, password_hash: str
    ) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
        )
        self.db_session.add(user)
        await self.db_session.flush()

        return user

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.db_session.execute(statement)

        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.db_session.execute(statement)

        return result.scalar_one_or_none()
