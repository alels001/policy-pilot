"""API tests: login, tokens and that /ask always uses the role from the token.

The RAG pipeline is replaced by a fake, so these tests need no database, no model and no
OpenAI key. They are fast and free, which matters when they run on every pull request.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from policy_pilot import api
from policy_pilot.generation import Answer

PASSWORD = "test-password"
SECRET = "test-secret-for-the-api-tests-only-0123456789"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("DEMO_PASSWORD", PASSWORD)
    return TestClient(api.app)


@pytest.fixture
def roles_asked(monkeypatch):
    """Replace the RAG pipeline with a fake that records the role it was called with."""
    roles = []

    def fake_answer(question: str, role: str) -> Answer:
        roles.append(role)
        return Answer(text=f"answer for {role}", sources=[], answered=True)

    monkeypatch.setattr(api, "answer", fake_answer)
    return roles


def auth_header(client: TestClient, user_id: str) -> dict[str, str]:
    response = client.post("/login", json={"user_id": user_id, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_with_wrong_password_fails(client):
    response = client.post("/login", json={"user_id": "u-anna", "password": "wrong"})
    assert response.status_code == 401


def test_unknown_user_gets_the_same_error_as_wrong_password(client):
    unknown = client.post("/login", json={"user_id": "nobody", "password": PASSWORD})
    wrong = client.post("/login", json={"user_id": "u-anna", "password": "wrong"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_me_returns_the_role_from_the_token(client):
    response = client.get("/me", headers=auth_header(client, "u-jonas"))
    assert response.json()["role"] == "hr_specialist"


def test_ask_without_token_is_rejected(client, roles_asked):
    response = client.post("/ask", json={"question": "Wie viele Urlaubstage habe ich?"})
    assert response.status_code == 401
    assert roles_asked == []


def test_ask_uses_the_role_from_the_token(client, roles_asked):
    response = client.post(
        "/ask", json={"question": "Salary band?"}, headers=auth_header(client, "u-anna")
    )
    assert response.status_code == 200
    assert roles_asked == ["employee"]


def test_ask_rejects_a_role_in_the_request(client, roles_asked):
    response = client.post(
        "/ask",
        json={"question": "Salary band?", "role": "hr_specialist"},
        headers=auth_header(client, "u-anna"),
    )
    assert response.status_code == 422
    assert roles_asked == []


def test_ask_rejects_an_empty_question(client, roles_asked):
    response = client.post("/ask", json={"question": ""}, headers=auth_header(client, "u-anna"))
    assert response.status_code == 422


def test_forged_token_is_rejected(client, roles_asked):
    payload = {
        "sub": "u-anna",
        "name": "Anna Becker",
        "role": "hr_specialist",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    forged = jwt.encode(payload, "a-different-secret-the-attacker-guessed-0123", algorithm="HS256")
    response = client.post(
        "/ask", json={"question": "Salary band?"}, headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401
    assert roles_asked == []


def test_expired_token_is_rejected(client, roles_asked):
    payload = {
        "sub": "u-anna",
        "name": "Anna Becker",
        "role": "employee",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    expired = jwt.encode(payload, SECRET, algorithm="HS256")
    response = client.get("/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"
