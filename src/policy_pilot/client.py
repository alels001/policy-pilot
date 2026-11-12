"""Small HTTP client for the PolicyPilot API, used by the chat UI."""

import httpx

from policy_pilot import config

TIMEOUT = httpx.Timeout(60.0)  # an answer can take several seconds


class ApiError(Exception):
    """The API could not be reached or returned an error."""


class NotSignedIn(ApiError):
    """Wrong login, or the token is missing, expired or invalid."""


def _request(method: str, path: str, token: str | None = None, json: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = httpx.request(
            method, f"{config.API_URL}{path}", json=json, headers=headers, timeout=TIMEOUT
        )
    except httpx.TransportError as error:
        raise ApiError(f"The API is not reachable at {config.API_URL}.") from error
    if response.status_code == 401:
        raise NotSignedIn(response.json().get("detail", "Not signed in"))
    if response.is_error:
        raise ApiError(f"The API returned an error ({response.status_code}).")
    return response.json()


def login(user_id: str, password: str) -> str:
    response = _request("POST", "/login", json={"user_id": user_id, "password": password})
    return response["access_token"]


def get(path: str, token: str):
    return _request("GET", path, token=token)


def ask(question: str, token: str, conversation_id: str | None = None) -> dict:
    body = {"question": question}
    if conversation_id:
        body["conversation_id"] = conversation_id
    return _request("POST", "/ask", token=token, json=body)
