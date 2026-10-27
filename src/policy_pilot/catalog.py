"""Read the document catalog: which documents exist, which version is current, who may read them."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    path: str
    department: str
    classification: str
    allowed_roles: tuple[str, ...]
    version: str
    valid_from: str
    status: str
    language: str
    owner: str


def load_catalog(data_dir: Path) -> list[Document]:
    raw = yaml.safe_load((data_dir / "catalog.yaml").read_text(encoding="utf-8"))
    known_roles = set(raw["roles"])

    documents = []
    for entry in raw["documents"]:
        unknown = set(entry["allowed_roles"]) - known_roles
        if unknown:
            raise ValueError(f"{entry['doc_id']}: unknown roles {sorted(unknown)}")

        documents.append(
            Document(
                doc_id=entry["doc_id"],
                title=entry["title"],
                path=entry["path"],
                department=entry["department"],
                classification=entry["classification"],
                allowed_roles=tuple(entry["allowed_roles"]),
                version=str(entry["version"]),
                valid_from=str(entry["valid_from"]),
                status=entry["status"],
                language=entry["language"],
                owner=entry["owner"],
            )
        )
    return documents


def current_documents(documents: list[Document]) -> list[Document]:
    """Only current versions are indexed. Superseded versions never reach the search."""
    return [doc for doc in documents if doc.status == "current"]
