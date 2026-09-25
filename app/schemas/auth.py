import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

LowerEmail = Annotated[EmailStr, AfterValidator(str.lower)]


class AuthResponse(BaseModel):
    user_id: uuid.UUID


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: LowerEmail
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(AuthResponse): ...


class LoginRequest(BaseModel):
    email: LowerEmail
    password: str


class LoginResponse(AuthResponse): ...


class MeResponse(BaseModel):
    user_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
