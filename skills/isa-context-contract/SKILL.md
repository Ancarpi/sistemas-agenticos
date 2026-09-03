---
name: isa-context-contract
description: "Write or audit the Context Contract of a model call, a channel or a boundary between agents, against the schema rather than from memory, and reject any contract that declares allowed data without its forbidden data. Use when you say '/isa-context-contract', 'escribe el contrato de contexto', 'audita el contrato del nodo', 'contrato de conversación', 'write the context contract', 'audit this node contract', or a node calls a model with nothing declared."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "[llamada | canal | frontera] [ruta del nodo]"
effort: medium
model: sonnet
category: domain
---

# /isa-context-contract — the security interface of a model call

A contract here is not documentation: it is the interface that decides what reaches a model and what a model may reach. You either write one that validates, or you audit calls that have none. Both end in a file, not in advice.

## Canon

Read both before you write, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/patterns/context-contract.md` — the three scopes (per call, per channel, per boundary), what each field is for, and the antipattern.
- `schemas/context-contract.schema.json` — the field names and the `required` set. The schema is the authority on shape; the pattern file on intent.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — fix the scope first

Which of the three scopes the pattern file names applies here: a **call** (one node, one model invocation), a **channel** (what a user is promised and what may be asked of them), or a **boundary** (one agent handing work to another). The scope decides which fields exist — a boundary contract that omits the authority the receiver is granted is not a boundary contract.

## Step 2 — fill it from the schema, never from memory

Open the schema, walk its `required` keys, and fill each one from the node's real code and state keys — read the node before you declare its contract. Leave nothing implicit: an unset limit is an unlimited limit.

## Step 3 — the refusals

Stop and report instead of writing when:

- allowed data is declared and forbidden data is not. The forbidden list is the minimisation the pattern file describes; a contract with only an allow list has declared nothing.
- the allowed state keys do not exist in the graph state, or the visible tools are not in the agent's `tools_allowed`. A contract that does not match reality is worse than none, because it will be believed.
- limits or fallback are absent for a node that calls a model in a user-facing path.

Say which field is missing, why the canon requires it, and what you need to fill it.

## Step 4 — validate, then assert it in code

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/tools/isa_validate/isa_validate.py" context-contract <contrato>.yaml
```

`isa_validate` reads YAML or JSON, never Python, so what you validate is the contract as data: either the file the node loads, or the serialization of the typed object (`model_dump()` dumped to YAML). Exit 0 or it is not written. Then wire it: the contract is constructed next to the node and checked **before** the call — forbidden patterns matched against the assembled input, visible tools bound from the contract, output validated against the declared schema, limits passed to the client. A contract that only exists as a comment is the antipattern the canon names.

## Step 5 — audit mode

When the argument is a repo or a path, invert the flow: find the model calls and report the ones without a contract.

```bash
grep -rn "get_model\|invoke(\|ainvoke(\|\.stream(" <path> --include=*.py
```

For each hit: contract present or absent, and if present, whether it is asserted or decorative. Report as a table ordered by exposure — user-facing and tool-carrying nodes first.

## Output contract

In Spanish:

```
ALCANCE: llamada | canal | frontera · <nodo/canal/frontera>
CONTRATO: <ruta escrita>  ·  VALIDACIÓN: exit <0|1>
ASEVERADO EN: <fichero:línea del chequeo previo a la llamada>
RECHAZOS: <campo> — <por qué el canon lo exige>
AUDITORÍA: <n> llamadas, <n> sin contrato, <n> con contrato decorativo
```

## Out of scope

Tools and their manifests (`/isa-tool-manifest`), the level of the actions a node can trigger (`/isa-autonomy-gate`), scaffolding the graph around the contract (`/isa-scaffold-agent`), and hunting leaks across an existing codebase — that is the `isa-context-leak` lens, which reads and never writes.
