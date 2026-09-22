from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao
from app.services.auth_service import AuthService


def get_auth_service(
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    user_dao = UserDao(db_session)
    auth_session_dao = AuthSessionDao(db_session)
    return AuthService(user_dao, auth_session_dao)
