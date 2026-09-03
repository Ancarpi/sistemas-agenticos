---
name: isa-criterio
description: "Answer a criterion question from the package canon: route over knowledge/INDEX.md, return the rule as its file states it plus the book locator, and say plainly when the canon does not hold it. Use when you say '/isa-criterio', 'qué criterio aplica', 'qué dice el libro sobre', 'cuál es la regla de', 'what is the rule for', 'which criterion applies here', or you want to read the canon instead of running a task."
user-invocable: true
allowed-tools: Read, Grep, Glob
argument-hint: "[tema o palabra clave]"
effort: low
model: haiku
category: meta
---

# /isa-criterio — what criterion applies here

The reader arm of this package, and the half of the brief that says *for people to learn from*. You resolve a topic to the file in `knowledge/` that owns it and surface the rule from there. You never restate a rule in words of your own, and you never produce one the canon does not hold.

## Canon

Read these before answering, resolved from the plugin root (`${CLAUDE_PLUGIN_ROOT}/<path>`):

- `knowledge/INDEX.md` — the routing table, and the twelve architect rules with the file that expands each one.
- the file the routing table points at. That file, not this one, is the answer.

Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.

## Step 1 — route

Match the topic to a row of `INDEX.md`. If two rows fit equally, show both and ask — never pick silently. If no row claims it, grep the bodies before concluding anything:

```bash
grep -rin "<term>" "${CLAUDE_PLUGIN_ROOT}/knowledge/"
```

## Step 2 — read narrowly, answer from the file

Read the file the row names (whole file only if it is short; otherwise `offset` around the hit). Then answer in Spanish with three things and nothing else:

1. the rule as its file states it — the enunciado, its why, and the antipattern that violates it;
2. the `> Origen:` locator of that file, so the reader can open the book at the right module;
3. the `knowledge/` path, so the next agent loads the rule instead of trusting this answer.

If the question is about **data** — a field name, an enum value, a checklist item, a level's controls — the answer lives in `schemas/`, not in `knowledge/`. Name the schema file and quote the entry; prose about data drifts, data does not.

## Step 3 — a miss is a real miss

The grep already read every body, so an empty result means the canon genuinely does not hold it. Say so plainly, and say where it would live: `knowledge/protocols/` for a discipline, `knowledge/patterns/` for a shape that gets implemented, `schemas/` if it is data. Then stop.

**Never fill the gap from memory.** A rule this package asserts without holding is worse than a gap: it looks like the book and is not. Point the user at the book instead.

## Step 4 — if they wanted the artefact, not the rule

| They want | Route to |
|---|---|
| a governed agent scaffolded | `/isa-scaffold-agent` |
| a context contract written or audited | `/isa-context-contract` |
| a tool manifest | `/isa-tool-manifest` |
| a level and its required controls | `/isa-autonomy-gate` |
| a release gate | `/isa-eval-gate` |
| a threat matrix with residual risk | `/isa-threat-model` |
| obligations and the evidence that is missing | `/isa-aiact-dossier` |
| a review of existing code | the lenses in `agents/isa/` |

## Out of scope

Writing or editing any artefact, and editing `knowledge/` itself. A rule that deserves to exist is a change to the canon, made deliberately — not a side effect of a lookup.
