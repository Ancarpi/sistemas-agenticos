---
slug: release-gate
owners:
  - isa-eval-gate
  - isa-eval-superstition
---

# Protocol — the release gate that is not a superstition

> Origen: 15.6, A·G.2, A·D·9, A·D·11

R11 of the architect's twelve: a threshold with no sample size and no passes per case is not a gate. You are measuring a non-deterministic system with a non-deterministic instrument, so a gate is six fields, not a number.

## 1. A gate declares six fields, or it is not a gate

`metric` · `dataset and its version` · `n_cases` · `passes_per_case` · `threshold` · `min_detectable_effect` (the difference considered real)

**Why** — the first three fix what was measured, the next two fix how much noise the measurement carries, and the last one is what turns a number into a decision.
**Violated by** — `Recall@5 >= 0.8` on its own; a dataset referenced by path with no version; a threshold agreed in a meeting and never written into the card.
**Checked by** — `schemas/eval-card.schema.json` makes `n_cases`, `passes_per_case` and `min_detectable_effect` **required**; `tools/isa_validate/isa_validate.py` exits non-zero. The refusal is validation, not the model's memory.

## 2. Size the dataset for the drop you care about, before fixing the threshold

**Why** — the relation is quadratic: detecting a 10-point drop with 20 cases is reasonable, detecting a 2-point drop with 20 cases is impossible. With 20 cases, two flipped cases move the metric 10 points.
**Violated by** — picking the threshold first and the corpus second; a gate at 0.80 over 20 cases, which blocks releases by chance and passes regressions by chance in similar proportions.
**Checked by** — skill `isa-eval-gate` computes the detectable drop for the proposed sample and states it before any threshold is written; lens `isa-eval-superstition` flags a gate whose corpus cannot see the drop it claims.

## 3. A single pass is an observation, not a measurement — report an interval

**Why** — the same case, prompt and model give different results across runs; "0.84 varying between 0.81 and 0.87 over five passes" says something, "0.84" says nothing.
**Violated by** — `passes_per_case: 1` reported as a measurement; a dashboard number with no dispersion.
**Checked by** — `passes_per_case` required in the eval card; the report carries mean, min, max and dispersion per metric.

## 4. Treat between-run variance as a metric of its own

**Why** — an agent that swings five points between identical runs is unstable even when its mean clears the gate, and instability is what reaches the user.
**Violated by** — averaging the swing away and shipping.
**Checked by** — variance is a declared metric in the card with its own threshold.

## 5. Three noise sources, and all three are yours to bound

Sampling noise (how many cases) · execution noise (how many passes) · judge noise (how calibrated the judge is).

**Why** — naming them separately is what stops a team from "fixing" judge disagreement by enlarging the corpus.
**Violated by** — attributing every fluctuation to "the model being non-deterministic" and stopping there.
**Checked by** — each source maps to a field: `n_cases`, `passes_per_case`, judge version plus its agreement score.

## 6. Calibrate the LLM judge before using it, and version it like the agent

**Why** — a judge is a second non-deterministic system measuring the first; and when you change the judge model your historical series stop being comparable, so a jump in the metric may just be a new thermometer.
**Violated by** — an uncalibrated judge in a release gate; a judge model upgraded silently; comparing variants of very different length, since a judge scores long answers and answers in its own style better.
**Checked by** — hand-label a subset, record judge/human agreement, and store the judge id and version in the eval card. Lens `isa-eval-superstition`.

## 7. "Not conclusive" is a legitimate verdict — and it means widen the sample

**Why** — when the drop falls inside the noise margin, "pass" and "fail" are both lies; the honest output distinguishes a regression from a fluctuation.
**Violated by** — a binary gate that forces a verdict; a debate replacing more cases.
**Checked by** — the gate's decision enum includes the non-conclusive outcome, and its documented consequence is to extend the corpus, not to argue.

## 8. Every production bug becomes an eval, a runbook or a policy (R9)

**Why** — in agents, what does not enter an evaluation comes back as an incident; a prompt fix with no test is a fix you cannot defend at the next release.
**Violated by** — a post-mortem that closes with "improved the prompt"; a hotfix merged without a case added to the golden set.
**Checked by** — the gate runs in CI on every pull request (`banco/.github/workflows/agent-evals.yml`, 25.5), and the incident is closed by a versioned artifact change (36.5).

## 9. Retrieval gates are release gates

**Why** — `Recall@k` obeys the same six fields as any other metric; a RAG gate exempted from them is the same superstition with a different name.
**Violated by** — a chunking change shipped because "it looks better".
**Checked by** — `patterns/knowledge-governance.md`.
