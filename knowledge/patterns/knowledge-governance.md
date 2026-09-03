---
slug: knowledge-governance
owners:
  - isa-eval-gate
  - isa-context-leak
---

# Pattern — knowledge governance

> Origen: 8.3, M24.1, M24.2, M24.3, M24.4, A·D·4

R4 of the architect's twelve: a RAG with no retrieval evaluation is not corporate knowledge, it is hope. What changes in a corporation is not the pipeline — it is that every step of it has an owner, a version and a date.

## 1. Evaluate two planes, not one

Retrieval — do I bring back the right chunks: `Recall@k`, `MRR`, `nDCG`, against a set of questions with their ground-truth documents. Generation — is the answer faithful and useful: faithfulness, answer relevancy, context precision and recall.

**Why** — a faithful answer over the wrong chunk and a hallucination over the right one are different defects with different fixes, and one aggregate number hides both.
**Violated by** — "it seems to work"; measuring only the final answer; a golden set with no ground-truth documents, which makes retrieval unmeasurable.
**Checked by** — both planes have their own metrics in the eval card; skill `isa-eval-gate`.

## 2. The retrieval gate obeys the same six fields as any other gate

**Why** — `Recall@5 >= 0.8` with no sample size, no passes per case and no minimum detectable effect is the same superstition under a different name.
**Violated by** — a chunking or embedding-model change shipped because the number looked better on twenty questions.
**Checked by** — `protocols/release-gate.md`; `schemas/eval-card.schema.json` requires `n_cases`, `passes_per_case` and `min_detectable_effect`.

## 3. Touching chunking, embeddings or the index re-runs the gate

**Why** — those three are the parameters that move recall most, and they are the ones changed casually because they feel like tuning rather than release.
**Violated by** — a reindex deployed with no baseline comparison; an embedding model swap with no ADR.
**Checked by** — the gate blocks the merge (8.3); model or corpus changes carry an ADR and a baseline comparison (`schemas/adr.template.md`, 25.5).

## 4. Nine metadata fields, because these are the ones that change results

`source_id` (traceability and citations) · `owner` (quality accountability) · `version` (stops mixing superseded rules) · `valid_from` / `valid_to` (freshness and expiry) · `jurisdiction` (legal applicability) · `product` (business filters) · `security_class` (permissions) · `chunk_type` (text, table, figure, FAQ) · `parent_section` (contextual expansion).

**Why** — every one of them is a filter that removes a wrong answer class; without `valid_to` the system confidently cites a repealed rule.
**Violated by** — metadata as an untyped JSON blob with no index, which turns every filter into a sequential scan; ingestion with no owner, so nobody can be asked whether a document is still current.
**Checked by** — business filters are typed columns with a composite index (7.6); the ingestion pipeline rejects a document missing a required field.

## 5. Push the permission filter as close to the index as possible

**Why** — if you retrieve first and filter in the application, you have already exposed restricted content to the process. A filter the application builds can be forgotten; a database policy cannot.
**Violated by** — post-filtering results in Python; a tenant filter passed as an optional argument; an application connecting as superuser or with bypass privileges, which skips row-level security entirely.
**Checked by** — the permission filter is a row-level policy evaluated whether or not anyone passes it (24.3); the application role is non-superuser and non-bypass. Lens `isa-context-leak`.

## 6. A chunk the subject may not see is a context leak, not a relevance problem

**Why** — vector search does not forgive badly designed permissions, and the failure presents itself as a good answer.
**Violated by** — treating an over-permissive retrieval as tuning; measuring only recall and never ACL denials.
**Checked by** — `security_class`, tenant, role, product and jurisdiction are part of the filter; ACL denials are a monitored metric (`protocols/observability-contract.md`).

## 7. Citations respect permissions

**Why** — you cannot cite a document the user is not allowed to see; the citation exfiltrates its existence, its title and often its content.
**Violated by** — a citation list built before the permission filter; a "source unavailable" note that still names the file.
**Checked by** — citations are derived from the already-filtered result set; citation coverage in regulated answers is a monitored metric.

## 8. Every stage of the lifecycle has an owner, a version and a date

Acquisition (document, owner, licence, classification, validity, authoritative source) · enrichment (metadata, contextual summary, entities, jurisdiction, product, version, links) · publication (versioned collection, index canary, rollback, corpus changelog) · retirement (expired documents, erasure requests, revoked permissions, cache cleanup).

**Why** — a corpus with no changelog cannot explain why an answer changed, and a corpus with no retirement path accumulates the documents that will contradict it.
**Violated by** — reindexing in place with no canary and no rollback; deleting a document and leaving its embeddings; a corpus version absent from the trace.
**Checked by** — `rag.corpus` and `rag.version` in every trace; the erasure path covers chunks and embeddings (`protocols/memory-governance.md`, store 6 of 7).

## 9. The golden set includes tables, figures and footnotes

**Why** — corporate documents hold fee tables, annexes, screenshots, diagrams and exceptions; a RAG evaluated only on paragraphs of prose will look reliable until it fails on the case that matters.
**Violated by** — a golden set built by sampling body text; a parser accepted with no OCR quality measurement before indexing.
**Checked by** — the dataset carries cases whose answer lives in a row, a footnote or a figure (24.4); `chunk_type` makes their coverage countable.

## 10. If the answer lives in a table, it is not RAG — it is a parameterized query

**Why** — retrieving a number that a `SELECT` returns exactly trades a correct answer for a plausible one.
**Violated by** — indexing a balances table into the corpus; a "what is my balance" question answered from chunks.
**Checked by** — structured data is served by a typed tool with its own manifest (8.6, `patterns/tool-capability.md`).
