from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import get_auth_service
from app.core.config import get_settings
from app.core.exceptions import DuplicateEmailException
from app.schemas.auth import RegisterRequest, RegisterResponse
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
