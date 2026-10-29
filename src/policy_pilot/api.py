"""PolicyPilot REST API.

Run from the project root:
    uv run uvicorn policy_pilot.api:app --reload
"""

from fastapi import FastAPI

from policy_pilot.db import connect

app = FastAPI(title="PolicyPilot API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check: the API runs and can reach the database."""
    with connect() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}