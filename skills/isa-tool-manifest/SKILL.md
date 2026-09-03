---
name: isa-tool-manifest
description: "Write the Tool Capability Manifest a tool needs before a model ever sees it, straight from the schema: owner, risk_tier, preconditions, effects, idempotency, approvers, timeouts, audit and rollback, with dry-run split from commit when the tier demands it. Use when you say '/isa-tool-manifest', 'escribe el manifiesto de la herramienta', 'ficha de capacidad', 'nueva herramienta con efecto', 'write the tool manifest', 'capability manifest for this tool', or a tool with effects has none."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[nombre de la herramienta] [ruta del módulo]"
effort: medium
model: sonnet
category: domain
---

# /isa-tool-manifest — the control document a tool ships with

The manifest exists so that security, architecture and the business can review a capability without reading its implementation. It is written **before** the tool is exposed to a model, and it is versioned with the code. You produce `<tool>.capability.yaml` and prove it validates.

## Canon

Read all three, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/patterns/tool-capability.md` — what a tool must have before production, the read/plan/dry-run/commit separation, idempotency, rollback and typed errors.
- `knowledge/protocols/autonomy-ladder.md` — how the tier of an action is graded, and by what variable.
- `schemas/tool-capability.schema.json` — the field names and the `required` set that make a manifest valid.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — interrogate the tool, not the developer's summary

Read the implementation if it exists. Establish, with evidence: what it reads, what it writes, what events it emits, whether the same call twice produces the same effect twice, what undoes it, and who is allowed to authorise it. Where the answer is "nobody knows yet", that is the finding — write it down and stop, rather than inventing a plausible manifest.

## Step 2 — get the tier from the gate, not from taste

The `risk_tier` is graded by the effect on the world. Run `/isa-autonomy-gate` on the action and take its level and required controls as input here. A tier chosen because the tool "feels internal" is exactly the drift the `isa-autonomy-drift` lens is built to catch.

## Step 3 — emit the manifest from the schema

Walk the schema's `required` keys and fill each from Step 1. Keep field names verbatim and in English — they are the vocabulary the platform, the CI and the policy engine share, so a translated key is a broken integration.

## Step 4 — the refusals are validation, not opinion

Run it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/tools/isa_validate/isa_validate.py" capability <tool>.capability.yaml
```

A manifest with no idempotency key and duplicate behaviour, or no rollback, **does not validate** and therefore is not written — the schema refuses, not you. Report the missing keys by name and what you need to fill them. Never soften this into a recommendation: that difference is the difference between a rule and a suggestion.

## Step 5 — split the phases when the tier demands it

Where the canon requires the phases separated, the manifest and the code must agree: a dry-run entry point that validates and returns the impact without writing, and a commit entry point that takes an idempotency key, writes inside a transaction, records to the outbox and to the audit log, and requires the declared approval. Errors return as typed, actionable tool errors — never a raw traceback, never an opaque boolean — so the agent can correct itself and the metrics can tell a bad argument from a downstream outage.

Register the tool where the platform can revoke it without redeploying agents. A capability that can only be disabled by shipping code is not governed.

## Output contract

In Spanish:

```
HERRAMIENTA: <name> v<version> · owner: <owner> · risk_tier: <tier> (L<n>)
MANIFIESTO: <ruta>  ·  VALIDACIÓN: exit <0|1>
EFECTOS: escribe <...> · emite <...>
IDEMPOTENCIA: <key> → <duplicate_behavior>   ROLLBACK: <tipo> vía <herramienta>
FASES: read | plan | dry-run | commit — <las que existen en código>
FALTA: <campo required sin valor> — <qué hace falta para cerrarlo>
```

## Out of scope

Grading the level (`/isa-autonomy-gate`), the contract of the node that calls the tool (`/isa-context-contract`), the graph around it (`/isa-scaffold-agent`), the threat matrix (`/isa-threat-model`), and auditing tools already written — the `isa-autonomy-drift` and `isa-idempotence` lenses do that, read-only.
