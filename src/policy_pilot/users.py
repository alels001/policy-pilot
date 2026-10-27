"""Demo users. In production, identity and role come from the company login (e.g. Entra ID)."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class User:
    user_id: str
    name: str
    department: str
    role: str


def load_users(data_dir: Path) -> list[User]:
    raw = yaml.safe_load((data_dir / "users.yaml").read_text(encoding="utf-8"))
    return [User(**entry) for entry in raw["users"]]
