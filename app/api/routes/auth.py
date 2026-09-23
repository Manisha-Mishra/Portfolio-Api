from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.services.auth import change_user_password, login_user, register_user, update_user_profile, user_from_token

router = APIRouter()
bearer = HTTPBearer()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=2_000_000)
    theme: Literal["system", "light", "dark"] | None = None


class PasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


@router.post("/auth/register")
def register(request: RegisterRequest):
    return register_user(request.name, request.email, request.password)


@router.post("/auth/login")
def login(request: LoginRequest):
    return login_user(request.email, request.password)


@router.get("/auth/me")
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    return {"user": user_from_token(credentials.credentials)}


@router.patch("/auth/profile")
def update_profile(
    request: ProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user = user_from_token(credentials.credentials)
    return {"user": update_user_profile(user["id"], request.name, request.avatar_url, request.theme)}


@router.post("/auth/password")
def update_password(
    request: PasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    user = user_from_token(credentials.credentials)
    change_user_password(user["id"], request.current_password, request.new_password)
    return {"message": "Password updated successfully."}