from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
    ) -> Account: ...

    async def get_account_by_id(
        self, user_id: UUID, account_id: UUID
    ) -> Account | None: ...

    async def list_accounts_by_user(self, user_id: UUID) -> list[Account] | None: ...

    async def update_mapping(
        self, user_id: UUID, account_id: UUID, mapping: dict[str, Any]
    ) -> bool: ...
