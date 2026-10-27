from pathlib import Path

import pytest

from policy_pilot.catalog import current_documents, load_catalog

DATA = Path("data")


def test_superseded_versions_are_excluded():
    current = current_documents(load_catalog(DATA))
    titles = {doc.title for doc in current}
    assert "Urlaubsrichtlinie 2026" in titles
    assert "Urlaubsrichtlinie 2025" not in titles


def test_confidential_documents_are_restricted():
    for doc in load_catalog(DATA):
        if doc.classification == "confidential":
            assert "employee" not in doc.allowed_roles, doc.doc_id


def test_unknown_role_stops_the_pipeline(tmp_path):
    (tmp_path / "catalog.yaml").write_text(
        """
roles: [employee]
documents:
  - doc_id: X-1
    title: Test
    path: x.md
    department: hr
    classification: internal
    allowed_roles: [employe]
    version: "1"
    valid_from: 2026-01-01
    status: current
    language: en
    owner: HR
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown roles"):
        load_catalog(tmp_path)
