"""Demo login and JWT tokens.

In production the company identity provider (e.g. Entra ID) signs the user in and issues
the token. This module plays that role for the demo, so the rest of the API works the same.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from policy_pilot import config
from policy_pilot.users import User, load_users

ALGORITHM = "HS256"
bearer = HTTPBearer()


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    name: str
    role: str


def find_user(user_id: str) -> User | None:
    return next((u for u in load_users(config.DATA_DIR) if u.user_id == user_id), None)


def authenticate(user_id: str, password: str) -> User | None:
    user = find_user(user_id)
    if user is None or not secrets.compare_digest(password, config.demo_password()):
        return None
    return user


def create_token(user: User) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user.user_id,
        "name": user.name,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.jwt_secret(), algorithm=ALGORITHM)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> CurrentUser:
    """Read the user from the signed token. The role never comes from the request."""
    try:
        payload = jwt.decode(credentials.credentials, config.jwt_secret(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None
    return CurrentUser(user_id=payload["sub"], name=payload["name"], role=payload["role"])
