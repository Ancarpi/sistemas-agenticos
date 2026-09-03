---
slug: tool-capability
owners:
  - isa-tool-manifest
  - isa-autonomy-drift
  - isa-idempotence
---

# Pattern — tools as governed capabilities

> Origen: M20.1, M20.2, M20.3, M20.4, A·D·5, A·D·8

R5 of the architect's twelve: a tool with no owner, schema, permissions and tests does not enter production. The manifest's JSON Schema is `schemas/tool-capability.schema.json`; a manifest without an idempotency key and a rollback does not validate.

## 1. The manifest exists before the tool is exposed to a model, and is versioned with the code

**Why** — it is the control document that lets security, architecture and the business review a capability without reading the implementation.
**Violated by** — a manifest written after the incident; a manifest in a wiki while the code moves.
**Checked by** — `tools/isa_validate/isa_validate.py` in CI over every `*.capability.yaml`; the manifest sits next to the code and carries its own `version`.

## 2. Twelve blocks, and each one exists because something failed without it

`name` · `version` · `owner` · `risk_tier` · `intent` · `auth` (subject required, scopes) · `preconditions` · `effects` (writes, emitted events) · `idempotency` (key, duplicate behaviour) · `approval` (human required, allowed approvers) · `timeouts` (p95, hard) · `audit` (args, result, PII fields) · `rollback`.

**Why** — owner answers who to call, tier answers how afraid to be, preconditions answer when it is legal, effects answer what to compensate, idempotency answers what a retry does, approval answers who signs, timeouts answer when to stop waiting, audit answers what is provable, rollback answers how to undo.
**Violated by** — `owner: platform` (a queue, not a person); an intent that restates the name; `effects` listing only the happy path.
**Checked by** — the schema marks `owner`, `risk_tier`, `idempotency.key`, `idempotency.duplicate_behavior` and `rollback` as required.

## 3. `risk_tier` is a rung of the ladder, not an adjective

**Why** — the tier is the same scale the policy engine resolves and the agent package declares; a private vocabulary makes the tier unenforceable.
**Violated by** — `risk_tier: medium`; a tier chosen so the tool avoids a control.
**Checked by** — the enum is bound to `schemas/autonomy-levels.yaml` (`protocols/autonomy-ladder.md`); lens `isa-autonomy-drift` compares the declared tier against what the code does.

## 4. Split the action into read, plan, dry-run and commit

| Phase | Who decides | What it may do | Control |
|---|---|---|---|
| Read | Code / tool | Query authoritative state | RBAC, rate limit, data minimization |
| Plan | Model | Propose an action and a reason | Structured output, policy, evaluation |
| Dry-run | Code | Simulate effects, validate preconditions | Writes nothing; returns an impact diff |
| Commit | Code, plus a human where required | Execute the transaction | Idempotency key, outbox, audit log |

**Why** — most tool incidents come from mixing computation and effect. The model may see and invoke the first three; the commit is fired by code only.
**Violated by** — one tool that computes and writes; a dry-run reachable only as a flag on the commit; a commit callable directly by the model at an irreversible tier.
**Checked by** — two separate entry points with separate names at tiers that require it; lens `isa-autonomy-drift` reports a commit reachable with no prior dry-run.

## 5. The idempotency key is a business key, and duplicate behaviour is declared

**Why** — the process will be retried, and processing the same unit twice must not duplicate the effect. A key built from a timestamp or a UUID never collides, so it never deduplicates.
**Violated by** — `key: uuid4()`; a key with no tenant or subject, which collides across customers; no `duplicate_behavior`, leaving the second call's semantics to whoever reads the code.
**Checked by** — the key is composed of business fields (subject + resource + reason + window); the commit looks it up inside the transaction and returns the stored result (20.2). Lens `isa-idempotence`.

## 6. Rollback is a named compensating action, not a hope

**Why** — an irreversible effect across systems cannot be rolled back by a database transaction; it is compensated by another tool that exists and has been tested.
**Violated by** — `rollback: manual`; a compensation that names a team instead of a capability; a compensation that has never been executed.
**Checked by** — `rollback.tool` resolves to a real capability with its own manifest; the compensation is exercised in tests (`patterns/backend-reliability.md`, sagas).

## 7. Errors are a coordination language: typed, compact, actionable

Codes: `INVALID_ARGUMENT` · `NOT_FOUND` · `AUTHZ_DENIED` · `PRECONDITION_FAILED` · `TRANSIENT_UPSTREAM` · `PERMANENT_UPSTREAM` · `POLICY_BLOCKED`, each with a safe message, a `retryable` flag and a suggested next step.

**Why** — the agent can only self-correct if it understands what failed, and the taxonomy is also a metric: "the model sent bad arguments" and "the core banking system is down" are not the same alert.
**Violated by** — raising a traceback at the model; returning `False`; a message containing PII or internal detail; a permanent failure marked retryable, which produces a loop.
**Checked by** — the error is returned as a tool message, never as a raw exception (20.3); tool error taxonomy is a monitored metric (`protocols/observability-contract.md`).

## 8. Above roughly forty tools you need a catalogue, not a better prompt

**Why** — availability depends on context — authentication, channel, jurisdiction, risk, case state, budget — and `risk_tier` is the metadata that orders the catalogue on its own: read and analysis with minimal auth and minimized output; reversible writes with policy, idempotency and audit log; the irreversible not offered at all without the four-phase barrier.
**Violated by** — every tool visible in every call; selection done by prompt instructions.
**Checked by** — dynamic selection reads the catalogue's metadata; the per-call offer is the visible-tools field of `patterns/context-contract.md`.

## 9. Share governed capabilities, not monolithic agents (R8)

**Why** — a published artifact is an execution surface: the platform can load it, measure it, block it, deprecate it and route traffic to it. A merely documented one does not exist operationally.
**Violated by** — sharing a prompt or a graph with no owner, version, tests, scope, rollback and activation criterion; a catalogue used as a wiki.
**Checked by** — each catalogue entry carries owner, version, risk, scopes, lifecycle state and a link to its tests (M33); the platform can revoke it without redeploying its consumers (`protocols/policy-over-model.md`, R10).
