---
slug: policy-over-model
owners:
  - isa-autonomy-gate
  - isa-threat-model
  - isa-autonomy-drift
---

# Protocol — the policy decides, the model does not

> Origen: M26.2, M35.2, A·D·2, A·D·10

The load-bearing sentence of the book, quoted as written: **«El modelo puede recomendar; la política decide.»** (26.2). Everything below is that sentence turned into checkable rules.

## 1. Authorization lives outside the LLM

Six classes of rule that never live in a prompt: authorization by role, economic limits, data classification, geographic blocking, mandatory HITL, and tool availability.

**Why** — a rule inside the context window is a rule the context window can be talked out of; indirect prompt injection makes that a matter of time, not of luck (16.1).
**Violated by** — "you must never transfer more than 100 EUR" written in a system prompt; a limit checked by reading the model's own argument instead of the authoritative record.
**Checked by** — the policy engine is a separate component with its own tests; a test must show the model cannot bypass the block even when it asks explicitly. Lens `isa-autonomy-drift`.

## 2. The engine returns one of five decisions

`allow` · `deny` · `require_human` · `require_dry_run` · `require_step_up_auth`

**Why** — a boolean engine can only permit or forbid, so every intermediate case degrades into "permit"; the three middle decisions are where graduated autonomy is actually implemented (`protocols/autonomy-ladder.md`).
**Violated by** — `authorize() -> bool`; an engine whose only refusal is an exception with no machine-readable reason.
**Checked by** — the decision type is an enum in the policy contract; the value is emitted into the trace as `policy.decision`.

## 3. The request carries subject, agent, tool, resource, context and risk

**Why** — RBAC answers what role the subject holds, ABAC answers what the situation is; a platform needs both, because "support role" plus "unauthenticated customer" plus "closed case" plus "prod" is one decision, not four (35.2).
**Violated by** — an engine that only receives the tool name; authorization decided before the resource owner is known.
**Checked by** — the six blocks are required fields of the authorization request; a call missing one fails closed.

## 4. Fail closed, and never let the caller supply its own verdict

**Why** — an engine that is unreachable and answers `allow` is worse than no engine, because it produces evidence of a control that was not applied.
**Violated by** — `except Exception: return allow`; a decision cached without its risk inputs; a decision passed as a tool argument the model can write.
**Checked by** — an engine-down test that asserts the action is refused.

## 5. The agent may explain a denial; it may not decide whether the denial applies

**Why** — explaining is a user-experience job and belongs in the conversation; deciding is a control and belongs in code.
**Violated by** — a tool that returns "not allowed, but you can retry with `force=true`"; a refusal the model can re-ask its way past inside the same turn.
**Checked by** — typed `ToolError` with `code: POLICY_BLOCKED` and `retryable: false` (`patterns/tool-capability.md`).

## 6. A mitigation that only exists in the prompt is not a control

**Why** — a control is something that holds when the prompt is ignored; the architecture is the primary security control, not the wording (16.1).
**Violated by** — a threat-model row whose control column reads "instruct the model not to".
**Checked by** — skill `isa-threat-model` demands the architectural equivalent for every prompt-only mitigation, and records "unmitigated" when there is none.

## 7. The platform can block a tool or an MCP server without redeploying agents (R10)

**Why** — if revoking a capability needs a release, the response time to an incident is a deploy pipeline, and the incident does not wait.
**Violated by** — an allow-list compiled into the agent image; a tool catalogue that only reloads on restart.
**Checked by** — a runtime test that removes a tool from the policy bundle and shows the running agent stops being offered it; `banco/plataforma/runtime.py` resolves policy per call (37.2).

## 8. Every decision is evidence, and evidence outlives the trace

**Why** — a denial nobody can prove happened is indistinguishable from a denial that never happened, and that difference is the whole audit.
**Violated by** — policy decisions logged only to stdout, or only to an observability backend with a 30-day retention.
**Checked by** — `policy.decision` in the trace for operations, and the Art. 12 register for legal evidence — they are different artifacts (`protocols/ai-act-map.md`, `protocols/observability-contract.md`).
