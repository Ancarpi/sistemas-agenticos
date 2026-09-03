---
slug: backend-reliability
owners:
  - isa-scaffold-agent
  - isa-idempotence
---

# Pattern — the autonomous backend

> Origen: 11.1, 11.3, M21.1, M21.2, M21.3, A·D·3

R3 of the architect's twelve: nothing irreversible without idempotency, dry-run or human approval, according to its risk. A backend agent is very autonomous and barely agentic — deterministic workflow outside, bounded islands of judgement inside.

## 1. The five commandments

Idempotency · retry with backoff and a dead-letter queue · hard limits · observability with an alert · asynchronous human-in-the-loop.

**Why** — each one names an incident class that has no other defence: duplicated effects, silent failures, a billing surprise at 3am, an act of faith, and an irreversible action taken because nobody was awake.
**Violated by** — four of the five; they do not substitute for each other.
**Checked by** — the sections below, one per commandment; lens `isa-idempotence`.

## 2. External effects need their own protection — the checkpointer is not enough

**Why** — LangGraph checkpointing resumes the graph, but creating a ticket or sending an email already happened; replaying the node repeats it.
**Violated by** — relying on the checkpointer as the idempotency mechanism; an idempotency key per run instead of per unit of work.
**Checked by** — an idempotency key per unit of work, stored in the same transaction as the effect (`patterns/tool-capability.md`); the acceptance test kills the process mid-batch and asserts no duplicate effect.

## 3. Transient failures retry with backoff and jitter; persistent failures go to dead-letter

**Why** — an unbounded retry against a downed dependency is a self-inflicted denial of service, and a swallowed failure is worse than a crash because nobody learns.
**Violated by** — a bare `except: pass`; retry with no maximum attempts; a dead-letter queue nobody reviews.
**Checked by** — `max_attempts`, backoff and jitter are declared in the retry policy; dead-letter entries have a human reviewer and each one becomes an eval case (`protocols/release-gate.md`, R9).

## 4. Hard limits per run and per batch: steps, tokens, euros, time

**Why** — an uncontrolled loop overnight is a billing incident, and the only limit that works is the one that stops the process.
**Violated by** — a budget that only alerts; a limit per call with none per batch; a `while True` with no step budget.
**Checked by** — the limit is enforced in code — the batch loop condition includes the spend check — and the run aborts, not warns (17.2).

## 5. Metrics per run, plus an alert on escalation and error rate

**Why** — an autonomous agent with no telemetry is an act of faith; and the two signals that reveal a broken night are the escalation rate and the tool error rate, not the exit code.
**Violated by** — a report emailed with no alerting path; latency measured as an average.
**Checked by** — processed, resolved, escalated, cost and p95 latency per run; `protocols/observability-contract.md`.

## 6. HITL is asynchronous: the agent queues and continues

**Why** — "no human contact" is the happy path, not the contract. A blocking wait ties up a worker and puts the batch's completion in a human's hands.
**Violated by** — a synchronous prompt in a background job; a `waiting_human` state that consumes a worker; an approval queue with no SLA or expiry.
**Checked by** — a durable interrupt resumed on the same thread; the job state machine below; the platform's HITL is one service shared by every channel, not a per-channel button (35.4).

## 7. A lease per case, a checkpoint per step, an outbox per effect

**Why** — the lease stops two workers processing the same case; the checkpoint stops repeating completed steps; the outbox stops losing side effects — you write "I must emit X" in the same transaction as the state, and a publisher delivers it with retries. This pattern matters more than any prompt.
**Violated by** — claiming a job with a plain `UPDATE` and no skip-locked select; a lease with no TTL and no renewal, so a dead worker holds the case forever; publishing an event before the transaction commits.
**Checked by** — the claim is one row, pessimistically locked, with a lease deadline (21.3); killing the worker mid-run and asserting another resumes without duplicating effects. Lens `isa-idempotence`.

## 8. Seven job states, and each one names who moves it

`pending` (producer; carries priority, type and SLA) · `leased` (worker; short TTL, renewed while work continues) · `running` (worker; checkpoint per thread) · `waiting_human` (HITL; consumes no worker) · `retry_scheduled` (policy; backoff, jitter, max attempts) · `completed` (worker; with result and evidence) · `dead_letter` (policy; human review, bug becomes eval).

**Why** — a two-state queue cannot express a paused approval or a scheduled retry, so both degrade into "running forever".
**Violated by** — a boolean `processed` column; a retry counter with no schedule.
**Checked by** — the state machine is enforced in the queue schema (`banco-meridiano/src/core/trabajos.py`), not in the worker's control flow.

## 9. Cross-system tasks are sagas: explicit compensations, every effect recorded

**Why** — background actions cross systems that share no transaction — core banking, CRM, email, ticketing, data lake — so there is nothing to roll back; there are compensations you designed and named.
**Violated by** — a "rollback" that assumes a single transaction; a partially applied task with no compensation for the steps that succeeded; a compensation with no test.
**Checked by** — each step declares its effect, its compensation and its agentic control (21.3); the compensation resolves to a real capability (`patterns/tool-capability.md`).

## 10. State outside the process, so the process is disposable

**Why** — horizontal scale, restarts and Kubernetes evictions are all the same requirement: the process must be replaceable mid-task.
**Violated by** — progress held in memory; a scheduler that assumes a single instance; a shutdown that drops in-flight work instead of draining it.
**Checked by** — Postgres holds state and checkpoints; the worker handles the termination signal, stops claiming and drains within the grace period (17.2).
