"""Database connection."""

import psycopg
from pgvector.psycopg import register_vector

from policy_pilot import config


def connect() -> psycopg.Connection:
    conn = psycopg.connect(**config.db_params())
    register_vector(conn)
    return conn
