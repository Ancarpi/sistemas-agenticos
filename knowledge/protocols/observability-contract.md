---
slug: observability-contract
owners:
  - isa-scaffold-agent
  - isa-eval-gate
---

# Protocol — the observability contract

> Origen: 15.1, M36.1, M36.2, M36.3, M36.4, A·D·7

R7 of the architect's twelve: an agent without `trace_id`, version and tool receipts is not auditable. This file is the criterion; the operational side of a specific backend (Langfuse metadata, cost per trace) lives in the sibling plugin `javbrain`, in `knowledge/observability.md`, and is not restated here.

## 1. Traces, not logs

**Why** — one request fans out into a dozen model calls, several tools and hops between agents; a flat log line cannot express the nesting, so it cannot answer "where did this go wrong".
**Violated by** — `print`; a log line per tool call with no run correlation; a span tree that stops at the framework boundary.
**Checked by** — each run is one hierarchical trace covering every model call (prompt, response, tokens, latency, cost), every tool (args, result, error) and every graph node. Subgraphs emit nothing unless explicitly enabled (A·D, M6).

## 2. Ten attributes, named identically by every team

`agent.id` / `agent.version` · `run.id` / `thread.id` · `tenant` / `env` / `region` · `model.alias` · `tool.id` / `tool.version` · `policy.decision` · `memory.read` / `memory.write` · `rag.corpus` / `rag.version` · `eval.scores` · `cost.total_eur`

**Why** — if one team writes `agent_name`, another `bot` and a third `workflow_id`, you cannot compare or alert across the fleet; the schema is what makes a fleet a fleet.
**Violated by** — per-project attribute names; a trace with no agent version, which makes a regression impossible to attribute; a provider model id where the alias belongs.
**Checked by** — the platform imposes the schema and propagates it to tracing, OpenTelemetry, SIEM and the data lake. `model.alias` carries the book's alias, never a provider identifier.

## 3. Tool receipts, not tool return values

**Why** — an auditable action needs to say who invoked it, under which policy decision, with which idempotency key, and what changed; a return value says none of that.
**Violated by** — a commit whose only evidence is the tool's response body; an approval with no signed receipt.
**Checked by** — `patterns/tool-capability.md` (audit block of the manifest); `protocols/policy-over-model.md` (`policy.decision` emitted per call).

## 4. PII, secrets and raw reasoning do not enter a trace

**Why** — a trace is replicated into corporate observability and read by people with no need to know; and the model's internal reasoning is not valid audit evidence anyway (2.5).
**Violated by** — full arguments logged verbatim; a masked answer whose tool result is unmasked in the span; reasoning tokens stored as the record of a decision.
**Checked by** — the manifest declares `log_args: masked` and `log_result: summary` plus the PII fields it touches; lens `isa-context-leak`.

## 5. The trace is not regulatory evidence

**Why** — traces are perishable by configuration (30 or 90 days); the legal record is the Art. 12 register and it outlives them by years. Confusing the two is the expensive mistake.
**Violated by** — a compliance dossier whose evidence field points at a tracing backend; a `trace_id` presented as proof that a notice was given.
**Checked by** — `protocols/ai-act-map.md`; the register's trace column is nullable on purpose.

## 6. Metrics live in five layers, and the top KPI is not cost per token

Business (autonomous resolution rate, escalation, cycle time, backlog) · quality (faithfulness, route accuracy, tool selection accuracy, task success) · security (injection detected, tool denied, PII blocked, policy bypass attempts) · operations (p95 latency, error rate, retry rate, queue age, checkpoint failures) · FinOps (cost per resolution, tokens per node, cache hit, fallback rate).

**Why** — if you only watch tokens you will optimize the wrong thing; the top-level KPI is cost per correct and safe resolution.
**Violated by** — a dashboard of token counts; a quality metric with no owner and no threshold.
**Checked by** — every metric declares owner and threshold; the report distinguishes engineering metrics from the ones a director reads.

## 7. Online evals sample by risk; offline evals block releases

**Why** — offline gates catch regressions before release, online evals catch degradation after it; neither substitutes for the other, and judging 100% of traffic with an LLM judge rarely pays for itself.
**Violated by** — online judging as the only quality signal; uniform sampling that under-watches high-risk traffic.
**Checked by** — sampling rates rise with risk (high risk evaluated by rules at full coverage), and each failure has a declared action: incident, annotation queue, or a pull request against the eval dataset (36.3).

## 8. An alert names corpus, agent, version, recent change and an example trace

**Why** — "faithfulness is low" is not actionable; the first action has to be obvious from the alert body.
**Violated by** — a threshold alert with no link and no diff; an alert with no runbook.
**Checked by** — the alert carries trace links, version diff, owners of agent/tool/corpus, its runbook, and the mitigation levers: block a tool, lower autonomy, activate a fallback, raise HITL, roll back.

## 9. Close the loop into a versioned artifact, never into a prompt tweak

**Why** — incident → reproducible trace → root-cause class → eval case → artifact fix → release gate → canary → monitoring is the only cycle that stops the same incident twice. What does not enter an evaluation comes back.
**Violated by** — a post-mortem that ends in "improved the prompt"; a fix with no test.
**Checked by** — `protocols/release-gate.md` (R9); the root-cause class is one of context, tool, model, orchestration or policy (36.5).
