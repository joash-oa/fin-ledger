import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator

LowerEmail = Annotated[EmailStr, AfterValidator(str.lower)]


class AuthResponse(BaseModel):
    user_id: uuid.UUID


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: LowerEmail
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower()


class RegisterResponse(AuthResponse): ...


class LoginRequest(BaseModel):
    email: LowerEmail
    password: str


class LoginResponse(AuthResponse): ...
