"""Central settings. Values come from environment variables / the .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
SCHEMA_FILE = Path(os.getenv("SCHEMA_FILE", "db/schema.sql"))

# Multilingual retrieval model: strong on German and English, runs locally, MIT license.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EEMBEDDING_DIM = 1024

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.4-mini")
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.5"))


def db_params() -> dict:
    """Connection settings for Postgres. The password is never written in the code."""
    return {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
    }