"""PolicyPilot REST API.

Run from the project root:
    uv run uvicorn policy_pilot.api:app --reload
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from policy_pilot import config
from policy_pilot.auth import CurrentUser, authenticate, create_token, current_user
from policy_pilot.db import connect

app = FastAPI(title="PolicyPilot API", version="0.1.0")


class LoginRequest(BaseModel):
    user_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check: the API runs and can reach the database."""
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest) -> TokenResponse:
    """Demo login. In production the company SSO issues the token."""
    user = authenticate(request.user_id, request.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong user or password")
    return TokenResponse(
        access_token=create_token(user),
        expires_in=config.JWT_EXPIRE_MINUTES * 60,
    )


@app.get("/me")
def me(user: Annotated[CurrentUser, Depends(current_user)]) -> CurrentUser:
    """Who am I? Shows what the API reads from the token."""
    return user