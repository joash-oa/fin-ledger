from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AccountMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posted_at: NonEmptyStr
    amount: NonEmptyStr
    description: NonEmptyStr
    running_balance: NonEmptyStr
    raw_type: NonEmptyStr
    date_format: Literal["YYYY MM DD", "MM DD YYYY", "DD MM YYYY"]
    row_order: Literal["asc", "desc"]
