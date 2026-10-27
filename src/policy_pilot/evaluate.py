"""Evaluate PolicyPilot on a labeled question set.

Run from the project root:
    uv run python -m policy_pilot.evaluate retrieval   # search only, no LLM, free
    uv run python -m policy_pilot.evaluate answers     # full pipeline with the LLM
"""

import csv
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from policy_pilot import config
from policy_pilot.catalog import current_documents, load_catalog
from policy_pilot.generation import answer
from policy_pilot.retrieval import search

GOLDEN_SET = Path("eval/golden_set.yaml")
THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50]


@dataclass(frozen=True)
class Case:
    id: str
    type: str
    role: str
    question: str
    expect: str
    doc_id: str | None = None
    must_contain: tuple[str, ...] = ()


def load_cases() -> list[Case]:
    raw = yaml.safe_load(GOLDEN_SET.read_text(encoding="utf-8"))
    return [
        Case(**{**entry, "must_contain": tuple(entry.get("must_contain", []))})
        for entry in raw["cases"]
    ]


def allowed_roles_by_doc() -> dict[str, set[str]]:
    documents = current_documents(load_catalog(config.DATA_DIR))
    return {doc.doc_id: set(doc.allowed_roles) for doc in documents}


def save(rows: list[dict], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nDetails saved to {path}")

def evaluate_retrieval(cases: list[Case]) -> list[dict]:
    """Search quality and a threshold sweep. No LLM calls, so it is free and fast."""
    allowed = allowed_roles_by_doc()
    rows = []
    for case in cases:
        results = search(case.question, case.role)
        top = max((r.similarity for r in results), default=0.0)  # same rule as generation.py
        found = {r.doc_id for r in results}
        rows.append(
            {
                "id": case.id,
                "type": case.type,
                "expect": case.expect,
                "top_similarity": round(top, 3),
                "expected_doc_found": case.doc_id in found if case.expect == "answer" else "",
                "leaked_chunks": sum(case.role not in allowed[r.doc_id] for r in results),
            }
        )

    answerable = [r for r in rows if r["expect"] == "answer"]
    refusals = [r for r in rows if r["expect"] == "refuse"]
    hits = sum(r["expected_doc_found"] for r in answerable)
    leaks = sum(r["leaked_chunks"] for r in rows)

    print(f"Expected document in top 5: {hits}/{len(answerable)}")
    print(f"Leaked chunks:              {leaks}")
    print("\nThreshold | answerable that reach the LLM | refusals stopped before the LLM")
    for threshold in THRESHOLDS:
        passed = sum(r["top_similarity"] >= threshold for r in answerable)
        stopped = sum(r["top_similarity"] < threshold for r in refusals)
        print(f"  {threshold:.2f}    | {passed:>2}/{len(answerable)}"
              f"                         | {stopped:>2}/{len(refusals)}")

    print("\nLowest similarity among answerable questions:")
    for r in sorted(answerable, key=lambda r: r["top_similarity"])[:5]:
        print(f"  {r['top_similarity']:.3f}  {r['id']}")
    print("Highest similarity among refusals:")
    for r in sorted(refusals, key=lambda r: r["top_similarity"], reverse=True)[:5]:
        print(f"  {r['top_similarity']:.3f}  {r['id']}")
    return rows    
def evaluate_answers(cases: list[Case]) -> list[dict]:
    """The full pipeline, as the user experiences it."""
    allowed = allowed_roles_by_doc()
    rows = []
    for case in cases:
        start = time.perf_counter()
        result = answer(case.question, case.role)
        seconds = time.perf_counter() - start

        cited = {source.doc_id for source in result.sources}
        if case.expect == "answer":
            text = result.text.lower()
            correct = (
                result.answered
                and case.doc_id in cited
                and any(fact.lower() in text for fact in case.must_contain)
            )
        else:
            correct = not result.answered

        rows.append(
            {
                "id": case.id,
                "type": case.type,
                "expect": case.expect,
                "correct": correct,
                "answered": result.answered,
                "cited_docs": ";".join(sorted(cited)),
                "leaked_docs": sum(case.role not in allowed[doc] for doc in cited),
                "seconds": round(seconds, 2),
                "answer": result.text.replace("\n", " "),
            }
        )
        print(f"{'PASS' if correct else 'FAIL'}  {case.id}")

    answerable = [r for r in rows if r["expect"] == "answer"]
    refusals = [r for r in rows if r["expect"] == "refuse"]
    answered = [r for r in rows if r["answered"]]
    with_sources = [r for r in answered if r["cited_docs"]]
    seconds = sorted(r["seconds"] for r in rows)

    print(f"\nThreshold (MIN_SIMILARITY): {config.MIN_SIMILARITY}")
    print(f"Correct answers:    {sum(r['correct'] for r in answerable)}/{len(answerable)}")
    print(f"Correct refusals:   {sum(r['correct'] for r in refusals)}/{len(refusals)}")
    print(f"Answers with source:{len(with_sources):>3}/{len(answered)}")
    print(f"Leaked documents:   {sum(r['leaked_docs'] for r in rows)}")
    print(f"Median time:        {seconds[len(seconds) // 2]:.1f} s")
    return rows
def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "retrieval"
    cases = load_cases()
    if mode == "retrieval":
        rows = evaluate_retrieval(cases)
    elif mode == "answers":
        rows = evaluate_answers(cases)
    else:
        raise SystemExit("Usage: python -m policy_pilot.evaluate [retrieval|answers]")
    save(rows, Path(f"eval/results_{mode}.csv"))


if __name__ == "__main__":
    main()