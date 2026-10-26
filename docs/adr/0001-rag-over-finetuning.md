# ADR-0001: Use Retrieval-Augmented Generation instead of fine-tuning

- **Status:** Accepted
- **Date:** 2026-10-26

## Context
PolicyPilot answers employee questions from internal HR, IT and Quality documents.
The PRD requires that answers:
- come only from approved, current documents,
- reference their sources,
- respect access rights per role,
- stay correct when documents change (policies yearly, audit reports per audit),
- work in German and English.

## Decision
We use Retrieval-Augmented Generation (RAG). Documents are split into chunks,
embedded and stored in a vector database together with access metadata.
At question time, only chunks the user is allowed to see are retrieved and passed
to a general-purpose LLM, which answers from them and cites them.
We do not fine-tune a model in the pilot.

## Alternatives considered

### 1. Fine-tune an LLM on the documents
- Knowledge is stored in the model weights, so access rights cannot be enforced
  per user: the model cannot "forget" confidential content for one user.
- No reliable source references.
- Every document update requires retraining, which is slow and costly.
- The model can still hallucinate, with no grounding to check against.

### 2. Put all documents into the prompt (long context)
- Sends all documents, including confidential ones, to the LLM for every question.
- Cost and latency grow with the number of documents.
- Answer quality drops with very long contexts.

## Consequences
**Positive**
- Access rights are enforced before the LLM sees any content.
- Every answer can reference its sources.
- Document updates only require re-indexing the changed documents.
- The LLM can be swapped (e.g. OpenAI, Azure OpenAI, a local model via Ollama).

**Negative**
- Answer quality depends on retrieval quality, so retrieval must be evaluated (Phase 7).
- Chunking and embedding choices need tuning.
- Extra components: ingestion pipeline and vector database.

**Revisit when**
Fine-tuning may be reconsidered later for tone or domain terminology,
not for storing knowledge.