---
slug: memory-governance
owners:
  - isa-memory-governance
  - isa-scaffold-agent
---

# Protocol — no memory without permission and expiry

> Origen: M34.1, M34.2, M34.3, M34.5, M34.6, A·D·6, A·D·12

R6 of the architect's twelve: memory with no provenance, expiry, sensitivity and permission is regulatory debt. "Agent memory" is seven different things with seven different owners; treating them as one store is where the debt is taken on.

## 1. Classify before you write: seven memories, seven controls

| Memory | What it holds | Who may write | Critical control |
|---|---|---|---|
| Working | State inside one run: plan, messages, partial results | The graph, during the run | Serializable checkpoint and size limits |
| Thread | History of one conversation or case | Runtime / checkpointer | Retention, PII, case closure, export |
| Individual | Authorized preferences and facts about a person | Agent with consent, or an authorized human | Consent, user editing, TTL, right to erasure |
| Domain | Patterns of an area: frequent incidents, approved exceptions, playbooks | Domain steward, after review | Owner, evidence, versioning |
| Collective | Institutional knowledge reused by many agents | Governed process: proposal → review → publication | Provenance, conflict, ACLs, evaluation |
| Procedural | How tasks are done: skills, runbooks, SOPs, prompts, subgraphs | Platform/domain team, via PR | Code review, evals, rollback |
| Episodic | Past events: traces, approvals, incidents, feedback | Runtime, automatically | Immutability, privacy, aggregation |

**Why** — the control that makes individual memory safe (user editing, TTL) is meaningless for episodic memory, whose control is the opposite (immutability); one store cannot satisfy both.
**Violated by** — a single `memories` table serving preferences, playbooks and audit events.
**Checked by** — every write declares its memory type and namespace; lens `isa-memory-governance`.

## 2. Expose typed operations, never a generic write

**Why** — `escribir_memoria(texto)` has no schema to validate, no policy to attach and no way to tell a preference from a policy candidate; it invites chaos by construction.
**Violated by** — one write tool with a free-text argument; a "notes" field that becomes the real memory.
**Checked by** — each operation has its own signature, validator and policy: record a declared preference (with its evidence), propose collective memory (which publishes nothing), forget an entry (with a typed reason). Each returns a receipt.

## 3. Every write carries its record fields

`namespace` · `key` · `value` · `source_run_id` · `sensitivity` · `confidence` · `ttl_days` · `consent_basis` · `owner` · `created_at` · `expires_at`

**Why** — these are the fields an auditor asks for one at a time; a memory that cannot answer "who wrote this, from what, under what basis, until when" is a hidden note, not corporate memory.
**Violated by** — a write with no `source_run_id` (unprovable), with no `sensitivity` (unclassifiable), or with `ttl_days: null` on personal data (undeletable by policy).
**Checked by** — the typed record is the API's argument type; a missing field is a validation error, not a warning.

## 4. The receipt matters as much as the write

A receipt answers: who proposed it, what source it used, what policy allowed it, when it expires, which agent will read it, and how it is reverted.

**Why** — without a receipt there is no traceability, and without traceability there is no corporate memory.
**Violated by** — a write that returns `True`; a deletion with no reason recorded.
**Checked by** — every memory operation returns a receipt object; `memory.read/write` appears in the trace (`protocols/observability-contract.md`).

## 5. Collective memory is born as a proposal, never written from a conversation

The path is: trace → memory candidate → steward queue → validation with evidence → versioned publication → non-regression eval.

**Why** — an agent may legitimately notice that ten incidents share a cause; turning that observation into operating policy without review is how one conversation rewrites the organization.
**Violated by** — a tool that publishes straight into the collective namespace; a "learned" fact promoted because confidence was high.
**Checked by** — the propose operation cannot publish; publication is a separate, human-authorized step. Lens `isa-memory-governance`.

## 6. Learning is a versioned artifact, not fine-tuning

Immediate and allowed: thread memory, explicit preferences, user feedback, trace annotation.
Deferred and governed: collective memory, prompt changes, new tools, policy changes, RAG reindexing.
Forbidden without review: inferring sensitive attributes, memorizing secrets, turning a model output into a source of truth, writing policy from an isolated conversation.

**Why** — "make the agent learn" is a word, not a mechanism; naming which of the seven mechanisms is meant is what makes it reviewable.
**Violated by** — continuous fine-tuning used as the primary memory or bug-fix mechanism.
**Checked by** — each learning path has a named artifact and a release gate (`protocols/release-gate.md`).

## 7. Personal data lives in seven stores — erasure is a distributed operation

Memory store · graph checkpoints · summaries · observability traces · audit register and approval receipts · RAG chunks and embeddings · job queue and outbox.

**Why** — erasure is not a `DELETE`; it needs an inventory of stores, an owner per store, a deadline per store, and proof that it ran. An embedding cannot be edited: it is reindexed. Summaries hide the datum as prose, where no field-level search will find it.
**Violated by** — a deletion path that touches only the store; a right-to-erasure procedure with no store inventory; a summary generated over unmasked text.
**Checked by** — the inventory exists as a document with owner and deadline per store, and the deletion is exercised end to end against a synthetic subject. Lens `isa-memory-governance`.

## 8. Erase the content, keep the fact

**Why** — the right to erasure and the duty to retain audit evidence point in opposite directions; the resolution is that the decision, its approver and its timestamp survive without the personal datum inside.
**Violated by** — deleting audit rows to satisfy an erasure request; or refusing the request because "the audit log is immutable".
**Checked by** — the register keeps the event and drops the content (`protocols/ai-act-map.md`, Art. 12); retention per store is a declared policy, not a shared default.

## 9. The personal datum you do not write is the only one you will not have to erase (R12)

Four habits that turn an impossible erasure into one `DELETE`: identifiers in state and traces, never values; sensitive data rehydrated inside the authorized tool and not returned to the context; summaries generated over already-masked text; documents containing personal data kept out of the general corpus.

**Why** — no deletion procedure is as reliable as an absent write.
**Violated by** — a full IBAN in a checkpoint; PII in a trace; a personal document indexed into the shared corpus.
**Checked by** — the forbidden-data field of the call's contract (`patterns/context-contract.md`); lenses `isa-context-leak` and `isa-memory-governance`.
