"""PolicyPilot REST API.

Run from the project root:
    uv run uvicorn policy_pilot.api:app --reload
"""

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from policy_pilot import config
from policy_pilot.auth import CurrentUser, authenticate, create_token, current_user
from policy_pilot.db import connect
from policy_pilot.generation import answer

app = FastAPI(title="PolicyPilot API", version="0.1.0")


class LoginRequest(BaseModel):
    user_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # e.g. a "role" field is rejected, not ignored

    question: str = Field(min_length=1, max_length=1000)


class Source(BaseModel):
    number: int
    doc_id: str
    title: str
    version: str
    section: str
    content: str


class AskResponse(BaseModel):
    answer: str
    answered: bool
    sources: list[Source]


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


@app.post("/ask")
def ask(request: AskRequest, user: Annotated[CurrentUser, Depends(current_user)]) -> AskResponse:
    """Answer a question for the signed-in user. The role comes from the token."""
    result = answer(request.question, user.role)
    sources = [
        Source(
            number=number,
            doc_id=s.doc_id,
            title=s.title,
            version=s.version,
            section=s.section,
            content=s.content,
        )
        for number, s in enumerate(result.sources, start=1)
    ]
    return AskResponse(answer=result.text, answered=result.answered, sources=sources)
