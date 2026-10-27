"""Find the chunks that best answer a question, among the chunks the user may see."""

import re
import sys
from dataclasses import dataclass

from policy_pilot.db import connect
from policy_pilot.embeddings import embed_query

TOP_K = 5
CANDIDATES = 20
RRF_K = 60

STOPWORDS = {
    "the", "and", "for", "what", "how", "many", "much", "can", "do", "does", "is", "are",
    "i", "my", "a", "an", "of", "to", "in", "on", "with", "get", "should", "must",
    "der", "die", "das", "und", "ich", "wie", "was", "viele", "habe", "ist", "sind",
    "ein", "eine", "für", "mit", "zu", "auf", "im", "in", "den", "dem", "des", "wo",
}


@dataclass(frozen=True)
class SearchResult:
    doc_id: str
    title: str
    version: str
    section: str
    content: str
    similarity: float
    score: float

SEARCH_SQL = """
WITH vector_hits AS (
    SELECT id, row_number() OVER (ORDER BY embedding <=> %(embedding)s) AS rank
    FROM chunks
    WHERE allowed_roles @> ARRAY[%(role)s]::text[]
    ORDER BY embedding <=> %(embedding)s
    LIMIT %(candidates)s
),
keyword_hits AS (
    SELECT id, row_number() OVER (ORDER BY ts_rank(content_tsv, query) DESC) AS rank
    FROM chunks, to_tsquery('simple', %(keywords)s) AS query
    WHERE allowed_roles @> ARRAY[%(role)s]::text[]
      AND content_tsv @@ query
    ORDER BY ts_rank(content_tsv, query) DESC
    LIMIT %(candidates)s
),
fused AS (
    SELECT id, sum(1.0 / (%(rrf_k)s + rank)) AS score
    FROM (
        SELECT id, rank FROM vector_hits
        UNION ALL
        SELECT id, rank FROM keyword_hits
    ) AS hits
    GROUP BY id
)
SELECT c.doc_id, c.title, c.version, c.section, c.content,
       1 - (c.embedding <=> %(embedding)s) AS similarity,
       f.score
FROM fused AS f
JOIN chunks AS c ON c.id = f.id
ORDER BY f.score DESC
LIMIT %(top_k)s
"""    

def keyword_query(question: str) -> str:
    """Turn a question into an OR keyword query: 'IATF Audit?' -> 'iatf | audit'."""
    words = re.findall(r"\w+", question.lower())
    keywords = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return " | ".join(dict.fromkeys(keywords))


def search(question: str, role: str, top_k: int = TOP_K) -> list[SearchResult]:
    params = {
        "embedding": embed_query(question),
        "keywords": keyword_query(question),
        "role": role,
        "candidates": CANDIDATES,
        "rrf_k": RRF_K,
        "top_k": top_k,
    }
    with connect() as conn:
        rows = conn.execute(SEARCH_SQL, params).fetchall()
    return [SearchResult(*row) for row in rows]


def main() -> None:
    """Debug helper: uv run python -m policy_pilot.retrieval <role> <question>"""
    role, question = sys.argv[1], " ".join(sys.argv[2:])
    for r in search(question, role):
        print(f"{r.score:.4f} | sim {r.similarity:.2f} | {r.doc_id} | {r.title} | {r.section}")


if __name__ == "__main__":
    main()