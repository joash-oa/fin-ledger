from app.daos.auth_session_dao import AuthSessionDao
from app.daos.user_dao import UserDao


class AuthService:
    def __init__(self, user_dao: UserDao, auth_session_dao: AuthSessionDao):
        self.user_dao = user_dao
        self.auth_session_dao = auth_session_dao
