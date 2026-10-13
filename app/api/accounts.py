from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_account_service, get_current_user
from app.core.exceptions import AccountNotFoundException, DuplicateAccountException
from app.schemas.accounts import (
    CreateAccountRequest,
    CreateAccountResponse,
    GetAccountResponse,
    ListAccountsResponse,
    PatchAccountRequest,
)
from app.services.account_service import AccountService
from app.services.auth_service import AuthenticatedUser

router = APIRouter(prefix="/accounts", tags=["accounts"])
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


@router.post(
    "", response_model=CreateAccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_account(
    body: CreateAccountRequest,
    current_user: CurrentUser,
    account_service: Annotated[AccountService, Depends(get_account_service)],
):
    try:
        account_id = await account_service.create_account(
            user_id=current_user.user_id,
            account_name=body.account_name,
            account_type=body.account_type,
            institution=body.institution,
            masked_number=body.masked_number,
        )
        return CreateAccountResponse(account_id=account_id)
    except DuplicateAccountException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
        ) from None


@router.get(
    "/{account_id}", response_model=GetAccountResponse, status_code=status.HTTP_200_OK
)
async def get_account(
    account_id: UUID,
    current_user: CurrentUser,
    account_service: Annotated[AccountService, Depends(get_account_service)],
):
    try:
        account_info = await account_service.get_account_by_id(
            user_id=current_user.user_id, account_id=account_id
        )
        return GetAccountResponse.model_validate(account_info, from_attributes=True)
    except AccountNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account exists with this ID",
        ) from None


@router.get("", response_model=ListAccountsResponse, status_code=status.HTTP_200_OK)
async def list_accounts(
    current_user: CurrentUser,
    account_service: Annotated[AccountService, Depends(get_account_service)],
):
    accounts = await account_service.list_accounts(user_id=current_user.user_id)
    return ListAccountsResponse.model_validate(accounts, from_attributes=True)


@router.patch("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_account(
    account_id: UUID,
    body: PatchAccountRequest,
    current_user: CurrentUser,
    account_service: Annotated[AccountService, Depends(get_account_service)],
):
    try:
        await account_service.update_account_mapping(
            user_id=current_user.user_id,
            account_id=account_id,
            mapping=body.mapping.model_dump(),
        )
    except AccountNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account exists with this ID",
        )
