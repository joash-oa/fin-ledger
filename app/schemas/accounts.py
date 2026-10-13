from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AccountMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posted_at: NonEmptyStr
    amount: NonEmptyStr
    description: NonEmptyStr
    running_balance: NonEmptyStr
    raw_type: NonEmptyStr
    date_format: NonEmptyStr
    row_order: Literal["asc", "desc"]


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
