FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_HTTP_TIMEOUT=300 \
    UV_CONCURRENT_DOWNLOADS=4 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Step 1: install only the libraries (cached until pyproject.toml or uv.lock change)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# Step 2: copy the code and install the project itself
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000 8501

CMD ["uvicorn", "policy_pilot.api:app", "--host", "0.0.0.0", "--port", "8000"]