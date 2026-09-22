from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.api.deps import get_auth_service
from app.core.config import get_settings
from app.core.exceptions import DuplicateEmailException, InvalidCredentialsException
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import AuthService, SessionToken

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def set_session_cookie(response: Response, token: SessionToken):
    response.set_cookie(
        key="session_token",
        value=token.value,
        max_age=token.max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    response: Response,
    body: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        auth_result = await auth_service.register(
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            password=body.password,
        )
        set_session_cookie(response, auth_result.session_token)
        return RegisterResponse(user_id=auth_result.user_id)
    except DuplicateEmailException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use"
        ) from None


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        auth_result = await auth_service.login(
            email=body.email,
            password=body.password,
        )
        set_session_cookie(response, auth_result.session_token)
        return LoginResponse(user_id=auth_result.user_id)
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session_token: Annotated[str | None, Cookie()] = None,
):
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    await auth_service.logout(session_token)
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
