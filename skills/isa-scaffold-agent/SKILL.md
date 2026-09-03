---
name: isa-scaffold-agent
description: "Scaffold a LangGraph agent that is governed from its first commit: checkpointer, gateway aliases, traces carrying trace_id and version, cost and step budgets, a context contract per node, typed memory and an agent.yaml that validates. Use when you say '/isa-scaffold-agent', 'levanta un agente', 'crea un agente gobernado', 'monta el grafo con gobierno', 'scaffold a governed agent', 'new LangGraph agent', or a graph is about to get its first tool with effects."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[nombre del agente] [ruta del proyecto]"
effort: medium
model: sonnet
category: domain
---

# /isa-scaffold-agent — a governed agent, not a graph that happens to run

You produce a graph whose governance exists before its first tool call: state, checkpointer, contracts, budgets, traces, typed memory, and the manifest that lets a platform publish it. Ungoverned scaffolding is what this skill exists to prevent, so the governance is not a later phase.

## Canon

Read all of these before writing a file, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/protocols/autonomy-ladder.md` — how the level of an action is graded, and the control each rung demands.
- `knowledge/patterns/context-contract.md` — the contract every model call declares, in its three scopes.
- `knowledge/patterns/backend-reliability.md` — what an autonomous worker needs to survive being killed.
- `knowledge/protocols/observability-contract.md` — what a run must carry to be auditable at all.
- `knowledge/protocols/memory-governance.md` — what a write to memory must declare before it happens.
- `knowledge/protocols/production-checklist.md` — the areas that gate production and who signs each one.
- `schemas/agent-package.schema.json` — the shape of the `agent.yaml` you will emit.
- `schemas/context-contract.schema.json` — the shape of each node's contract.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — gather, in one round

Ask for what the manifest schema declares `required` and nothing more: what the agent does, its owner and tenant, the channels it serves, the tools it may call **and which of them touch the world**, the memory scopes it reads and writes, and its SLO. Models are named by gateway alias only (`agente-rapido`, `agente-equilibrado`, `agente-listo`, `emb-multilingue`, `rerank-multilingue`) — a provider id in generated code is a defect, not a shortcut.

## Step 2 — refuse before you scaffold

If any declared tool has an effect outside the process and no autonomy level assigned, **stop and say so**. Run `/isa-autonomy-gate` on that tool first and come back with its level and required controls. A graph scaffolded around an ungraded effect is the incident this package is trying to prevent, and it is cheaper to refuse here than to review it later.

## Step 3 — the tree

Follow the project's existing layout when there is one. When there is none, the book's layout is the default: `src/core/` (models, contracts, policy, memory, jobs), `src/agents/<agent>/` (graph, tools), `src/channels/<channel>/` (the skin), `src/evals/`. `get_model()` lives in `src/core/models.py` and every node asks it for an alias — nothing else constructs a client.

Per node, emit its contract with `/isa-context-contract` and **assert it at run time before the call**, not in a docstring. Per tool with effects, emit its manifest with `/isa-tool-manifest`.

## Step 4 — wire the four things a graph cannot be retrofitted with

1. **Durability.** A checkpointer with a real `thread_id` derived server-side, never from client input; resume proven by killing the process mid-run.
2. **Budgets.** Hard step, token and euro ceilings per run, enforced in code, plus the failure they trigger when exceeded.
3. **Traces.** Every model and tool call carries the fields `observability-contract.md` requires; secrets and PII stay out of them, per the same file.
4. **Memory.** Typed APIs only, with owner, provenance, sensitivity and expiry per write, as `memory-governance.md` states. A generic write-anything function is not scaffolded here.

## Step 5 — the manifest, and the validation that is the actual gate

Emit `agent.yaml` and validate it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/tools/isa_validate/isa_validate.py" agent-package <path>/agent.yaml
```

Non-zero exit means it is not scaffolded yet. Report the missing `required` fields by name and fix them; never hand over a manifest you have not seen exit 0.

## Step 6 — close with what is still open

Read `schemas/production-checklist.yaml` and report every `blocking` item this agent does not yet satisfy, with its `owner_role`. Ending with an honest list of unsigned areas is the deliverable; claiming production readiness you did not verify is the one failure mode worse than an incomplete scaffold.

## Output contract

Give the user this, in Spanish:

```
AGENTE: <id> · <owner> · alias: <los que usa>
ESCRITO
  · <ruta> — <qué gobierna>
VALIDACIÓN: isa_validate agent-package → exit <0|1>
CONTRATOS: <n> nodos, <n> con contrato aseverado en ejecución
NIVELES: <herramienta> → L<n> (<controles presentes>)
ABIERTO Y BLOQUEANTE: <ítem del checklist> — <owner_role>
```

## Out of scope

Grading an action (`/isa-autonomy-gate`), the tool manifests themselves (`/isa-tool-manifest`), the release gate (`/isa-eval-gate`), the threat matrix (`/isa-threat-model`), the compliance dossier (`/isa-aiact-dossier`), and reviewing a graph already written — the lenses in `agents/isa/` do that read-only, `isa-memory-governance` for its memory writes and `isa-idempotence` for its effects.
