from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.daos.account_dao import AccountDao


@dataclass
class AccountInfo:
    account_id: UUID
    account_name: str
    institution: str
    account_type: str
    masked_number: str
    balance: int | None
    mapping: dict[str, Any] | None


@dataclass
class UserAccounts:
    accounts: list[AccountInfo]
    net_balance: int | None


class AccountService:
    def __init__(self, account_dao: AccountDao):
        self.account_dao = account_dao

    async def _get_account_balance(
        self, user_id: UUID, account_id: UUID
    ) -> int | None: ...

    async def create_account(
        self,
        user_id: UUID,
        account_name: str,
        account_type: str,
        institution: str,
        masked_number: str,
    ) -> UUID: ...

    async def get_account_by_id(
        self, user_id: UUID, account_id: UUID
    ) -> AccountInfo: ...

    async def list_accounts(self, user_id: UUID) -> UserAccounts: ...

    async def update_account_mapping(
        self, user_id: UUID, account_id: UUID, mapping: dict[str, Any]
    ) -> None: ...
