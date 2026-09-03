---
slug: autonomy-ladder
owners:
  - isa-autonomy-gate
  - isa-tool-manifest
  - isa-scaffold-agent
  - isa-autonomy-drift
---

# Protocol — the autonomy ladder L0-L4

> Origen: M21.4, A·H, M35.2, A·D·1

The canonical autonomy scale of the book. It is the `risk_tier` of a capability manifest (M20.1), the `autonomy_level` the policy engine resolves (M35.2), and the `risk_tier` of an Agent Package (M32.3) — one scale, three artifacts. The machine-readable matrix (autonomy, examples, required controls, forbidden practices) is `schemas/autonomy-levels.yaml`; read it from there, never from this prose.

## 1. Grade by effect on the world, never by trust in the model

**Why** — trust is an opinion that drifts with every model swap; effect is a property of the action and stays fixed.
**Violated by** — "the model is good enough now, let it commit", or a level raised because a demo went well.
**Checked by** — the level is a declared field in the manifest and the agent package, so it is reviewable; lens `isa-autonomy-drift` compares the declared level against what the code actually does.

## 2. Every action that leaves the process carries exactly one declared level

| Level | Effect on the world | Non-negotiable control |
|---|---|---|
| L0 | Read, no external effect | Logging and context limits |
| L1 | Draft or recommendation | Output validation and feedback |
| L2 | Dry-run or simulation | Evidence, estimated cost, **no commit** |
| L3 | Reversible commit | Idempotency, rollback, policy `allow` |
| L4 | Irreversible or regulated action | HITL, maker-checker, step-up auth — or prohibition |

**Why** — an undeclared level is a level nobody reviewed, and the review is the whole mechanism.
**Violated by** — a tool exposed to a model with no `risk_tier`; an agent whose `tools_allowed` reaches a tier above its own.
**Checked by** — `schemas/tool-capability.schema.json` (`risk_tier` required), `schemas/agent-package.schema.json`, `tools/isa_validate/isa_validate.py`.

## 3. L2 does not write

**Why** — the point of a dry-run is that its output is a diff of impact, not an impact; a dry-run that writes is a commit with a reassuring name.
**Violated by** — a "simulation" path that shares a transaction with the commit path, or that mutates state to compute its estimate.
**Checked by** — the read/plan/dry-run/commit separation in `patterns/tool-capability.md`; lens `isa-autonomy-drift`.

## 4. L3 requires all three: idempotency key, named rollback, policy allow

**Why** — reversible means somebody wrote down how to reverse it; without the key a retry duplicates the effect, and a retry will happen.
**Violated by** — `rollback: manual`, an empty rollback, or an idempotency key derived from a timestamp (a key that never repeats never deduplicates).
**Checked by** — `schemas/tool-capability.schema.json` requires `idempotency.key`, `idempotency.duplicate_behavior` and `rollback`; a manifest without them does not validate. Lens `isa-idempotence`.

## 5. L4 requires HITL, maker-checker or step-up auth — or it is forbidden

**Why** — an irreversible action with no human barrier has no ceiling on damage, so a single successful prompt injection is unbounded (16.1).
**Violated by** — approval by the same identity that proposed the action; an approval queue with no SLA or expiry; a "confirm?" turn inside the same conversation the attacker controls.
**Checked by** — `human_in_the_loop.required_for` in the agent package must list every L4 tool in `tools_allowed`; skill `isa-autonomy-gate` blocks on a missing control. An L4 with none of the three controls is not graduated autonomy: it is an incident with no date on it yet.

## 6. Maximum autonomy, minimum agency

**Why** — autonomy (runs with no human) and agency (freedom the model has to decide) are independent; buying autonomy with agency multiplies variance, cost and audit surface for nothing (11.1).
**Violated by** — a free-running tool loop where a deterministic workflow with bounded islands of judgement would do.
**Checked by** — step and token budgets per run (`patterns/backend-reliability.md`); the graph structure itself is the evidence.

## 7. Raising a level is a change of artifact, never a runtime decision

**Why** — if the model or the prompt can widen its own authority, the ladder is decoration.
**Violated by** — autonomy level read from model output; a policy that upgrades a tier because a retry failed; a level "temporarily" raised in production with no manifest bump.
**Checked by** — level lives in the versioned manifest and the policy bundle, and the policy decision is emitted into the trace as `policy.decision` (`protocols/observability-contract.md`).

## 8. Cap the level by economic value as well as by kind

**Why** — the same action is not the same risk at 50 EUR and at 50,000 EUR; a tier with no quantitative bound is a tier that was never really decided.
**Violated by** — a threshold that exists only in a prompt; an irreversible action with no amount limit and no compensation.
**Checked by** — the limit lives in the policy engine, not in the model (`protocols/policy-over-model.md`); the manifest declares its preconditions.
