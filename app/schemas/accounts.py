from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.mapping import AccountMapping, NonEmptyStr


class AccountInfoResponse(BaseModel):
    account_id: UUID
    account_name: str
    account_type: str
    masked_number: str
    institution: str
    balance: int | None


class CreateAccountRequest(BaseModel):
    account_name: NonEmptyStr
    account_type: Literal["checking", "savings"]
    masked_number: Annotated[str, Field(pattern="^[0-9]{4}$")]
    institution: NonEmptyStr

    @field_validator("account_type", mode="before")
    @classmethod
    def account_type_validator(cls, v) -> str:
        if isinstance(v, str):
            return v.lower()
        return v


class CreateAccountResponse(BaseModel):
    account_id: UUID


class GetAccountResponse(AccountInfoResponse):
    mapping: AccountMapping | None


class ListAccountsResponse(BaseModel):
    accounts: list[AccountInfoResponse]
    net_balance: int | None = None


class PatchAccountRequest(BaseModel):
    mapping: AccountMapping
