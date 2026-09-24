from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.exceptions import InvalidSessionException
from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao
from app.services.auth_service import AuthenticatedUser, AuthService

DBSession = Annotated[AsyncSession, Depends(get_db_session, scope="function")]


def get_auth_service(
    db_session: DBSession,
) -> AuthService:
    user_dao = UserDao(db_session)
    auth_session_dao = AuthSessionDao(db_session)
    return AuthService(user_dao, auth_session_dao)


async def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> AuthenticatedUser:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        user = await auth_service.authenticate(session_token)
        return user
    except InvalidSessionException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from None
