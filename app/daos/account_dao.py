from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateAccountException
from app.models import Account


class AccountDao:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_account(
        self,
        user_id: UUID,
        account_name: str,
        account_type: str,
        institution: str,
        masked_number: str,
    ) -> Account:
        account = Account(
            user_id=user_id,
            name=account_name,
            type=account_type,
            institution=institution,
            masked_number=masked_number,
        )
        self.db_session.add(account)

        try:
            await self.db_session.flush()
            return account
        except IntegrityError as ie:
            cause = ie.orig.__cause__
            if "ux_account" in str(cause):
                raise DuplicateAccountException
            else:
                raise

    async def get_account_by_id(
        self, user_id: UUID, account_id: UUID
    ) -> Account | None:
        statement = (
            select(Account)
            .where(Account.user_id == user_id)
            .where(Account.id == account_id)
        )
        result = await self.db_session.execute(statement)
        return result.scalar_one_or_none()

    async def list_accounts_by_user(self, user_id: UUID) -> list[Account]:
        statement = select(Account).where(Account.user_id == user_id)
        result = await self.db_session.execute(statement)
        return list(result.scalars().all())

    async def update_mapping(
        self, user_id: UUID, account_id: UUID, mapping: dict[str, Any]
    ) -> bool:
        statement = (
            update(Account)
            .where(Account.id == account_id)
            .where(Account.user_id == user_id)
            .values(mapping=mapping)
        )

        result = await self.db_session.execute(statement)
        row_count = result.rowcount
        return bool(row_count)
