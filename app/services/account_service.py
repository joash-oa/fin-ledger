from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.exceptions import AccountNotFoundException
from app.daos.account_dao import AccountDao
from app.models import Account


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

    async def _get_account_balance(self, account_id: UUID) -> int | None:
        # Update when transactions service is implemented
        return None

    async def _get_account_info(self, account: Account) -> AccountInfo:
        balance = await self._get_account_balance(account_id=account.id)
        return AccountInfo(
            account_id=account.id,
            account_name=account.name,
            institution=account.institution,
            account_type=account.type,
            masked_number=account.masked_number,
            mapping=account.mapping,
            balance=balance,
        )

    async def create_account(
        self,
        user_id: UUID,
        account_name: str,
        account_type: str,
        institution: str,
        masked_number: str,
    ) -> UUID:
        account = await self.account_dao.create_account(
            user_id=user_id,
            account_name=account_name,
            account_type=account_type,
            institution=institution,
            masked_number=masked_number,
        )
        return account.id

    async def get_account_by_id(self, user_id: UUID, account_id: UUID) -> AccountInfo:
        account = await self.account_dao.get_account_by_id(
            user_id=user_id, account_id=account_id
        )
        if account is None:
            raise AccountNotFoundException

        account_info = await self._get_account_info(account)
        return account_info

    async def list_accounts(self, user_id: UUID) -> UserAccounts:
        accounts = await self.account_dao.list_accounts_by_user(user_id=user_id)

        net_balance: int | None = None
        user_accounts = []

        for account in accounts:
            account_info = await self._get_account_info(account)
            user_accounts.append(account_info)

            if account_info.balance is not None:
                if net_balance is None:
                    net_balance = account_info.balance
                else:
                    net_balance += account_info.balance

        return UserAccounts(accounts=user_accounts, net_balance=net_balance)

    async def update_account_mapping(
        self, user_id: UUID, account_id: UUID, mapping: dict[str, Any]
    ) -> None:
        updated = await self.account_dao.update_mapping(
            user_id=user_id,
            account_id=account_id,
            mapping=mapping,
        )
        if not updated:
            raise AccountNotFoundException
