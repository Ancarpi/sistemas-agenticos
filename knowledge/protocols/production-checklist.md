---
slug: production-checklist
owners:
  - isa-aiact-dossier
  - isa-scaffold-agent
---

# Protocol — the pre-production gate

> Origen: A·F

Ten areas stand between a working agent and a production agent: architecture, tools, RAG/knowledge, memory, security, HITL, observability, deployment, operation, compliance. The items are data and live in `schemas/production-checklist.yaml`, with an `id`, an `owner_role` and a `blocking` flag each. This file is the rule for using them — which the checklist itself does not state.

## 1. It is a gate, not a retrospective

**Why** — a checklist reviewed after go-live documents the risk you already took; run before, it is the cheapest control in the package.
**Violated by** — running it during the post-mortem; running it once and never again after a substantial design change.
**Checked by** — the checklist run is a required step of the release, and a substantial design change restarts it.

## 2. Every area has an owner who signs, by name and date

**Why** — ten areas with one owner is one owner with no time; the signature is what converts a tick into an accepted responsibility.
**Violated by** — "reviewed by the team"; an area signed by whoever built it, with no second reader.
**Checked by** — `owner_role` per item in the schema; the run output is a table of area, owner, date and verdict.

## 3. An unsigned blocking area blocks — there is no "we will fix it after launch"

**Why** — the areas marked blocking are the ones whose absence is not recoverable by a later patch: irreversible actions with no approval, memory with no expiry, a corpus with no permissions.
**Violated by** — a launch with open blocking items and a promise; a `blocking: true` item downgraded to get a date.
**Checked by** — `blocking` is a field, so a script counts what is missing; skill `isa-aiact-dossier` reports the count and refuses to call a dossier complete while it is non-zero.

## 4. A tick cites its evidence

**Why** — "tools have tests" is an opinion until it names the test; the checklist's value is that an auditor can follow each row to an artifact.
**Violated by** — ticks with no path, no version and no test name.
**Checked by** — each item's evidence is a file path or a test identifier, the same discipline as the compliance dossier (`protocols/ai-act-map.md`).

## 5. Each area delegates to its own criterion — the checklist does not restate it

Architecture and tools → `patterns/tool-capability.md` · RAG/knowledge → `patterns/knowledge-governance.md` · memory → `protocols/memory-governance.md` · security → `protocols/agent-threat-model.md` · HITL and autonomy → `protocols/autonomy-ladder.md` and `protocols/policy-over-model.md` · observability → `protocols/observability-contract.md` · deployment eval gates → `protocols/release-gate.md` · compliance → `protocols/ai-act-map.md`.

**Why** — one rule, one home: an item that carries its own version of a rule is a second copy that will drift.
**Violated by** — a checklist row that spells out an idempotency requirement instead of pointing at it.
**Checked by** — every item resolves to exactly one criterion file.

## 6. Cite security lists by their current edition, and record which one you used

**Why** — the OWASP lists renumber between editions, so "OWASP-compliant" with no year is unverifiable a year later.
**Violated by** — an identifier with no year in a risk register.
**Checked by** — `protocols/agent-threat-model.md` fixes the editions in force and their dates.

## 7. Pick one operational-resilience regime, not two

**Why** — a financial entity complies with DORA as the special regime; a plan that maps to both DORA and NIS2 is a plan that has not decided.
**Violated by** — a compliance area listing both.
**Checked by** — `protocols/ai-act-map.md`; the choice is written in the dossier with its justification.

## 8. Operation is an area, not an afterthought

**Why** — SLOs, on-call, budgets and cost review are what make the difference between a system that survives its second month and one that quietly degrades.
**Violated by** — a launch with no SLO, no owner on call and no cost budget per run.
**Checked by** — the agent package declares its `slo` block (M32.3); budgets are enforced per run and per batch (`patterns/backend-reliability.md`).
