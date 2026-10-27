"""Build the search index: catalog -> chunks -> embeddings -> Postgres.

Run from the project root:
    uv run python -m policy_pilot.ingest
"""

from policy_pilot import config
from policy_pilot.catalog import Document, current_documents, load_catalog
from policy_pilot.chunking import split_markdown
from policy_pilot.db import connect
from policy_pilot.embeddings import embed_passages

INSERT_SQL = """
INSERT INTO chunks (
    doc_id, title, version, section, chunk_index, content, language,
    department, classification, allowed_roles, source_path, embedding
) VALUES (
    %(doc_id)s, %(title)s, %(version)s, %(section)s, %(chunk_index)s, %(content)s, %(language)s,
    %(department)s, %(classification)s, %(allowed_roles)s, %(source_path)s, %(embedding)s
)
"""


def build_rows(documents: list[Document]) -> list[dict]:
    rows = []
    for doc in documents:
        markdown = (config.DATA_DIR / doc.path).read_text(encoding="utf-8")
        for index, chunk in enumerate(split_markdown(markdown)):
            rows.append(
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "version": doc.version,
                    "section": chunk.section,
                    "chunk_index": index,
                    "content": chunk.text,
                    "language": doc.language,
                    "department": doc.department,
                    "classification": doc.classification,
                    "allowed_roles": list(doc.allowed_roles),
                    "source_path": doc.path,
                }
            )
    return rows


def main() -> None:
    documents = load_catalog(config.DATA_DIR)
    current = current_documents(documents)
    print(
        f"Catalog: {len(documents)} documents, {len(current)} current, "
        f"{len(documents) - len(current)} superseded (skipped)"
    )

    rows = build_rows(current)
    print(f"Chunks: {len(rows)}")

    texts = [f"{row['title']} - {row['section']}\n{row['content']}" for row in rows]
    vectors = embed_passages(texts)
    for row, vector in zip(rows, vectors):
        row["embedding"] = vector

    with connect() as conn:
        conn.execute(config.SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.execute("TRUNCATE chunks")
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)

    print(f"Indexed {len(rows)} chunks from {len(current)} documents.")


if __name__ == "__main__":
    main()
