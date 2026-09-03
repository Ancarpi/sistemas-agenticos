---
name: isa-aiact-dossier
description: "Map a system to its regulatory obligations and to the technical artefact each one demands: role before risk, risk classified per use case and never per model, then the evidence that exists in the repo, the evidence that is missing, and the production checklist counted. Use when you say '/isa-aiact-dossier', 'dossier de cumplimiento', 'qué exige el AI Act aquí', 'clasificación de riesgo', 'AI Act dossier', 'compliance evidence for this agent', or an audit is coming."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[sistema | ruta del repo]"
effort: high
model: sonnet
category: domain
---

# /isa-aiact-dossier — obligations, and the artefact each one demands

A dossier is not a memo about the regulation: it is the list of obligations that reach this system and, per obligation, the engineering artefact that satisfies it, where that artefact is, and the test that proves it still works. You end with what is missing, counted. A dossier that claims completeness it cannot show is the failure mode here — an unfinished one that names its gaps is useful.

## Canon

Read all four, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/protocols/ai-act-map.md` — obligation to artefact, the role distinction, how risk is classified, and the dated state of the framework.
- `knowledge/protocols/production-checklist.md` — the areas that gate production and the rule that each one is signed.
- `schemas/ai-act-obligations.yaml` — obligation, article, artefact demanded, and where the evidence lives. Walk these rows; they are the dossier's spine.
- `schemas/production-checklist.yaml` — the checklist items with their `owner_role` and whether they block.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — role first, then risk, and always per use case

Before any classification: which role this organisation holds for this system, and whether it holds more than one at once — the obligation lists differ. Then classify **per use case, never per model and never per service**: the same graph can sit in one risk class answering a chat and in a higher one scoring a customer. One entry per use case, including the ones that do not exist yet but are already planned.

## Step 2 — walk the obligations and hunt the evidence

For each row of `ai-act-obligations.yaml` that reaches this system, find the artefact in the repo. Grep, then read; a filename is not evidence.

| Obligación | Artículo | Artefacto exigido | Evidencia (fichero::símbolo) | Prueba | Estado |
|---|---|---|---|---|---|

`Estado` is `implementado` only with both evidence and a test that would fail if it regressed. Otherwise `parcial` or `ausente`. An obligation you cannot map is written as unmapped, with what it would take.

## Step 3 — the classification as a versioned file, not a document

Write or refresh the classification file the repo keeps, with its version, the date it was reviewed, the date of the next review, the framework it cites with its exact reference, and per system the role, the risk class, the grounds and the obligation entries with their evidence and their test. Then make it breakable: a test that fails when the next review date has passed, so the dossier cannot age in silence. A classification nobody can break is the way a compliance file becomes false without anyone lying.

## Step 4 — count the checklist

Read `schemas/production-checklist.yaml` and report, per area, the `blocking` items this system does not satisfy and the `owner_role` that has to sign each one. An unsigned blocking area blocks production; say so plainly rather than describing it as pending.

## Step 5 — dates or nothing

Every regulatory statement in the output carries its date and its locator, taken from the canon file. If the canon does not date a claim, the claim does not go in the dossier — an undated regulatory assertion is the one thing an auditor is guaranteed to test.

## Output contract

In Spanish, after the obligations table:

```
SISTEMA: <id> · papel: <el que corresponda> · riesgo: <clase> por <caso de uso>
MARCO: <referencia exacta con fecha, tomada del canon>
CLASIFICACIÓN: <ruta del fichero escrito> · revisado <fecha> · próximo examen <fecha>
IMPLEMENTADO: <n>  ·  PARCIAL: <n>  ·  AUSENTE: <n>
HUECOS
  · <obligación> — falta <artefacto> · lo cierra <skill o trabajo> · owner <rol>
CHECKLIST BLOQUEANTE SIN FIRMA: <área> — <ítem> — <owner_role>
```

## Out of scope

The threat matrix and its residual risk (`/isa-threat-model`), autonomy levels (`/isa-autonomy-gate`), the release gate the robustness obligation leans on (`/isa-eval-gate`), the code that implements an artefact (`/isa-scaffold-agent`, `/isa-tool-manifest`), and legal advice — this produces engineering evidence, and a lawyer reads it.
