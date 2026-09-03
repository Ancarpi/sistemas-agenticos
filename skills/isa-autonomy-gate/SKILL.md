---
name: isa-autonomy-gate
description: "Assign L0 to L4 to an action or an agent from the level data, then demand the controls that level requires and block when they are absent: no reversible commit without idempotency and rollback, no irreversible action without its mandatory control. Use when you say '/isa-autonomy-gate', 'qué nivel de autonomía', 'puede hacerlo sin humano', 'gradúa la autonomía', 'assign the autonomy level', 'can this run unattended', or an action needs its level before it ships."
user-invocable: true
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "[acción o agente a graduar]"
effort: high
model: sonnet
category: domain
---

# /isa-autonomy-gate — the level, and the controls that come with it

You return a level and a verdict. The level is graded by the **effect the action has on the world**, never by how much the model is trusted; the verdict is whether the controls that level demands are actually present. A level without its controls is a label, and this skill does not hand out labels.

## Canon

Read all three, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/protocols/autonomy-ladder.md` — the rungs, the grading variable, and why the last rung is the one that gets skipped.
- `knowledge/protocols/policy-over-model.md` — what must live outside the model, and the decisions the policy engine returns.
- `schemas/autonomy-levels.yaml` — the ladder as data: per level, its `required_controls[]` and its `forbidden[]`. Quote from here; do not paraphrase the controls.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — state the effect, in one line, before naming a level

Write what the action does to the world: what it reads, what it writes, who notices, whether it can be undone and by whom, and the economic or regulatory exposure of one wrong execution. If the input is a vague capability ("manage cases"), decompose it into the concrete actions first — a level is assigned to an action, and an agent inherits the highest level it can reach.

## Step 2 — pick the level from the data

Read `schemas/autonomy-levels.yaml` and select the level whose definition matches the effect. Justify it in one sentence against that definition. Where two rungs are arguable, take the higher one and say why the choice was close: over-grading costs a control, under-grading costs an incident.

## Step 3 — demand the controls, item by item

For the chosen level, list its `required_controls[]` verbatim from the YAML and check each against the specification in front of you, with evidence:

| Control | Present? | Evidence or what is missing |
|---|---|---|

An absent control is not a recommendation. Also check the level's `forbidden[]`: anything on that list appearing in the spec is an immediate block.

## Step 4 — say which decision the policy engine must return

The authorisation belongs outside the model. Name the decision the engine has to return for this action, from the set `policy-over-model.md` defines, and where that call is made in the code path. If the answer is "the agent decides", that is the finding: report it as a block, because the canon puts that rule above any convenience.

## Step 5 — the verdict, and where the level has to be written down

A level that is not recorded is a level that drifts. Say where it goes: the tool manifest's `risk_tier` (`/isa-tool-manifest`) and the agent manifest's `risk_tier` (`/isa-scaffold-agent`), plus the human-approval list where the level demands one.

## Output contract

In Spanish, lead with the verdict:

```
ACCIÓN: <qué hace en el mundo, una línea>
NIVEL: L<n> — <justificación contra la definición del YAML>
VEREDICTO: pasa | BLOQUEA — <control ausente>
CONTROLES EXIGIDOS
  · <control, verbatim del YAML> — presente <fichero:línea> | AUSENTE
PROHIBIDO EN ESTE NIVEL: <ítem de forbidden[] detectado> | ninguno
DECISIÓN DE POLÍTICA: <la que debe devolver el engine> · se decide en <ruta>
SE ESCRIBE EN: <manifiesto(s) y campo>
```

If it blocks, do not offer a workaround that removes the control. Offer the level below it, with what has to be given up to sit there.

## Out of scope

Writing the manifest that carries the tier (`/isa-tool-manifest`), the node contract (`/isa-context-contract`), the graph (`/isa-scaffold-agent`), the release gate (`/isa-eval-gate`), and grading a diff — a specification is graded here, code already written is the `isa-autonomy-drift` lens.
