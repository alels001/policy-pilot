-- One row per chunk. Every chunk carries the access rights of its document.
CREATE TABLE IF NOT EXISTS chunks (
    id              BIGSERIAL PRIMARY KEY,
    doc_id          TEXT         NOT NULL,
    title           TEXT         NOT NULL,
    version         TEXT         NOT NULL,
    section         TEXT         NOT NULL,
    chunk_index     INTEGER      NOT NULL,
    content         TEXT         NOT NULL,
    language        TEXT         NOT NULL,
    department      TEXT         NOT NULL,
    classification  TEXT         NOT NULL,
    allowed_roles   TEXT[]       NOT NULL,
    source_path     TEXT         NOT NULL,
    embedding       vector(1024) NOT NULL,
    content_tsv     tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', title || ' ' || section || ' ' || content)
    ) STORED
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_roles_idx ON chunks USING gin (allowed_roles);
CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (content_tsv);