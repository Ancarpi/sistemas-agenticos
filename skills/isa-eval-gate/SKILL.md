---
name: isa-eval-gate
description: "Write a release gate that can be trusted: every field the eval card schema requires, the drop the proposed sample can actually detect stated before the threshold is fixed, and a refusal to write the card at all when sample size or passes per case are missing. Use when you say '/isa-eval-gate', 'escribe la puerta de release', 'define el umbral', 'esta puerta es fiable', 'write the release gate', 'can I trust this threshold', or a number is about to block a release."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[métrica | ruta del eval card]"
effort: medium
model: sonnet
category: domain
---

# /isa-eval-gate — a threshold with a sample behind it, or no gate at all

A number that blocks a release has to survive the question *how would you know*. You produce an eval card that validates and a statement of what its sample can and cannot detect — and when the sample is not stated, you refuse to write the card. That refusal is this skill's whole value.

## Canon

Read these, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/protocols/release-gate.md` — what a gate must declare, the noise sources it has to survive, and the third verdict most teams do not have.
- `knowledge/protocols/observability-contract.md` — what the run has to emit for the gate's numbers to be reconstructible later.
- `knowledge/patterns/knowledge-governance.md` — retrieval gates obey the same discipline as any other; read this whenever the metric is a retrieval metric.
- `schemas/eval-card.schema.json` — the field names and the `required` set. This file, not your judgement, is what refuses an incomplete gate.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — collect the fields the schema requires, and stop if they are not there

Ask once, for exactly what the schema declares `required`. Then:

**If sample size or passes per case are missing, do not write the card.** Say what is missing, say that the schema makes it `required` and that `isa_validate` will exit non-zero without it, and ask for the number. Do not substitute a default, do not write a draft "to be completed", do not write the card with a comment. A gate whose sample nobody stated is the superstition `release-gate.md` names, and shipping it under this package's name is worse than having no gate.

The same applies to a dataset with no version: a threshold against a moving set measures the set, not the agent.

## Step 2 — say what the sample can detect, before fixing the threshold

Measure the noise instead of assuming it: run the existing set unchanged several times and report mean, min, max and dispersion per metric. Then state the smallest drop that clears that dispersion — and note that the relationship between the drop you want to catch and the cases you need is quadratic, so halving the detectable drop costs far more than twice the cases.

If the proposed set cannot detect the drop that actually matters to the owner, **say so in the report and say how many cases it would take.** Then fix the threshold, not before.

## Step 3 — write the card and validate it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/tools/isa_validate/isa_validate.py" eval-card <path>
```

Exit 0 or it is not a gate yet. Report missing `required` fields by name.

## Step 4 — the three things a gate needs that a card does not hold

1. **The inconclusive verdict.** Where a difference falls inside the noise, the gate's honest answer is neither pass nor fail — it is the verdict `release-gate.md` calls *no concluyente*, and the response to it is more sample, not more argument. Say explicitly which range of results produces it.
2. **A versioned judge.** If an LLM scores the results, its calibration and its version belong in the card. Changing the judge invalidates the historical series; record it as a version bump, not as an improvement.
3. **Wiring.** The gate runs where a release is decided (CI on every pull request, per the card's cadence), and it blocks. A card nobody executes is documentation.

## Output contract

In Spanish:

```
PUERTA: <nombre del eval card> · conjunto <nombre>@<versión>
CAMPOS (los required del esquema): <campo> = <valor> …
ESCRIBIBLE: sí | NO — falta <campo> (required en eval-card.schema.json)
RUIDO MEDIDO: media <x> · min <x> · max <x> · dispersión <x> en <p> pases
DETECTA: una caída de <x> puntos; por debajo, el veredicto es «no concluyente»
JUEZ: <modelo o humano> · calibración <valor> · versión <v> | no aplica
VALIDACIÓN: isa_validate eval-card → exit <0|1>
BLOQUEA EN: <dónde corre y qué release detiene>
```

## Out of scope

Building the dataset itself, the trajectory harness, the graph under test (`/isa-scaffold-agent`), red-team corpora (`/isa-threat-model`), and auditing gates already written — the `isa-eval-superstition` lens reads existing thresholds and never writes.
