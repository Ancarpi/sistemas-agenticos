---
slug: index
owners:
  - isa-criterio
---

# Knowledge index — the criterion of the book, routed

> Origen: A·D (las doce reglas), y el resto del libro por su localizador en cada fichero

The single map of "which rule lives where". This is the entry point: `isa-criterio` reads this table to resolve a question to one file; every other skill and lens loads its own files by relative path from its `## Canon` section. Twelve criterion files, one rule per file, and nothing duplicated between them.

Two audiences, one tree. A person reads this page and the twelve rules below and already has the criterion. An agent loads the target file at the moment of deciding — which is the only moment it changes an outcome.

**Data is not here.** Everything a tool consumes — the autonomy matrix, the JSON Schemas, the obligation map, the checklist items, the adversarial corpus, the templates — lives in `schemas/` and only there, so a schema cannot exist in two versions. `knowledge/` is Markdown criterion; `schemas/` is data.

## Routing table

| Keywords | Target file | Slug |
|---|---|---|
| autonomy, autonomía, autonomy level, nivel de autonomía, L0 L1 L2 L3 L4, escalera de autonomía, autonomy ladder, risk_tier, peldaño, irreversible action, acción irreversible, graduated autonomy, autonomía graduada, dry-run vs commit, mínima agencia, minimum agency, HITL requerido, maker-checker, step-up auth | `protocols/autonomy-ladder.md` | `autonomy-ladder` |
| policy engine, política, policy as code, quién autoriza, who authorizes, RBAC, ABAC, allow deny require_human, require_dry_run, require_step_up_auth, límite económico, spend limit, bloquear una herramienta, block a tool, fail closed, la política decide, prompt is not a control | `protocols/policy-over-model.md` | `policy-over-model` |
| release gate, puerta de release, umbral, threshold, tamaño de muestra, sample size, n_cases, passes_per_case, min detectable effect, eval card, superstición, superstition, LLM judge, juez, calibrar el juez, no concluyente, not conclusive, bug to eval, ruido de muestreo, intervalo | `protocols/release-gate.md` | `release-gate` |
| memoria, memory, memory governance, TTL, caducidad, procedencia, provenance, consentimiento, consent, working thread individual domain collective procedural episodic, receipt, escribir_memoria, memoria colectiva, collective memory, borrado, erasure, right to be forgotten, derecho al olvido, siete almacenes, seven stores | `protocols/memory-governance.md` | `memory-governance` |
| AI Act, EU AI Act, 2024/1689, 2026/1744, Digital Omnibus, Art. 50, Art. 12, Art. 14, alto riesgo, high risk, Anexo III, clasificación de riesgo, risk classification, dossier de conformidad, compliance dossier, RGPD, GDPR, minimización, DORA, NIS2, retención, retention, alfabetización en IA, AI literacy, registro, register | `protocols/ai-act-map.md` | `ai-act-map` |
| threat model, modelo de amenazas, OWASP, LLM01, ASI01, agentic top 10, prompt injection, inyección indirecta, indirect injection, riesgo residual, residual risk, sandboxing, sandbox, MCP security, A2A, tool poisoning, allow-list, pinning, red team, excessive agency | `protocols/agent-threat-model.md` | `agent-threat-model` |
| observabilidad, observability, trazas, traces, trace_id, spans, atributos de traza, trace schema, receipts, métricas por capa, metrics per layer, coste por resolución, cost per resolution, evals online, online evals, sampling por riesgo, alerta accionable, actionable alert, qué no va en una traza, deriva, drift | `protocols/observability-contract.md` | `observability-contract` |
| checklist de producción, production checklist, puerta previa, pre-production gate, diez áreas, ten areas, owner que firma, sign-off, blocking item, antes de producción, go live, launch readiness | `protocols/production-checklist.md` | `production-checklist` |
| context contract, contrato de contexto, context engineering, datos permitidos, allowed data, datos prohibidos, forbidden data, herramientas visibles, visible tools, límites de la llamada, fallback, conversation contract, contrato de canal, handoff contract, contrato de traspaso, authority, escalado a humano, human handoff, instrucciones y datos, instruction data separation | `patterns/context-contract.md` | `context-contract` |
| herramienta, tool, capability manifest, tool capability, manifiesto de capacidad, idempotencia, idempotency key, duplicate_behavior, rollback, compensating action, read plan dry-run commit, ToolError, errores tipados, typed errors, catálogo de herramientas, tool catalog, scopes, permisos dinámicos, capacidades gobernadas | `patterns/tool-capability.md` | `tool-capability` |
| backend, agente background, background agent, worker, cola, queue, lease, outbox, DLQ, dead letter, reintento, retry, backoff, saga, compensación, límites duros, hard limits, presupuesto, budget, estados de trabajo, job states, HITL asíncrono, batch nocturno, cinco mandamientos | `patterns/backend-reliability.md` | `backend-reliability` |
| RAG, conocimiento, knowledge engineering, Recall@k, faithfulness, evaluación de RAG, retrieval evaluation, metadata mínima, chunking, embeddings, permisos en RAG, RAG permissions, ACL, RLS, frescura, freshness, valid_from valid_to, procedencia del corpus, reindexación, reindex, citas, citations, tablas y figuras | `patterns/knowledge-governance.md` | `knowledge-governance` |

## Las doce reglas del arquitecto agéntico

The book's own index of criteria (A·D), quoted verbatim — the only prose in this package that is not distilled. Each rule links to the file that expands it into checkable form.

1. Usa la mínima agencia que resuelva el problema; cada libertad del modelo exige una eval y observabilidad. → [`protocols/autonomy-ladder.md`](protocols/autonomy-ladder.md)
2. El modelo decide; el código ejecuta; el policy engine autoriza. → [`protocols/policy-over-model.md`](protocols/policy-over-model.md)
3. Ninguna acción irreversible sin idempotencia, dry-run o aprobación humana según su riesgo. → [`patterns/backend-reliability.md`](patterns/backend-reliability.md)
4. Un RAG sin evaluaciones de recuperación no es conocimiento corporativo: es esperanza. → [`patterns/knowledge-governance.md`](patterns/knowledge-governance.md)
5. Una herramienta sin owner, esquema, permisos y tests no entra en producción. → [`patterns/tool-capability.md`](patterns/tool-capability.md)
6. Una memoria sin procedencia, caducidad, sensibilidad y permiso es deuda regulatoria. → [`protocols/memory-governance.md`](protocols/memory-governance.md)
7. Un agente sin trace_id, versión y receipts de herramienta no es auditable. → [`protocols/observability-contract.md`](protocols/observability-contract.md)
8. No compartas agentes monolíticos; comparte capacidades gobernadas. → [`patterns/tool-capability.md`](patterns/tool-capability.md)
9. Todo bug de producción debe convertirse en una evaluación, un runbook o una política. → [`protocols/release-gate.md`](protocols/release-gate.md)
10. La plataforma debe poder bloquear una herramienta o un MCP sin redesplegar agentes. → [`protocols/policy-over-model.md`](protocols/policy-over-model.md)
11. Un umbral sin tamaño de muestra ni pases por caso no es una puerta: es una superstición. → [`protocols/release-gate.md`](protocols/release-gate.md)
12. El dato personal que no escribes es el único que no tendrás que borrar. → [`protocols/memory-governance.md`](protocols/memory-governance.md)

Twelve rules, twelve homes, no orphan file and no homeless rule. Two files carry two rules each because those rules are two faces of one criterion: R5 and R8 are both "a capability is governed or it is not shared"; R9 and R11 are both "a gate is six fields or it is theatre"; R6 and R12 are both "memory you cannot govern is debt".

## The four criterion files outside the twelve

`protocols/ai-act-map.md`, `protocols/agent-threat-model.md`, `protocols/production-checklist.md` and `patterns/context-contract.md` are not in the twelve — they carry the criterion of the book's annexes and of the modules the twelve rules assume: what the regulation demands as an artifact, what the threat matrix must have in its third column, what has to be signed before production, and what a model call must declare. They are cited from the same skills.

## Adding a rule

One rule, one file, one row here.

```
Is it about how the discipline works? ........ protocols/
Is it a shape you implement in code? ......... patterns/
Is it data a tool consumes? .................. schemas/, not here
Is it under ~30 substantive lines? ........... fold it into its parent file
```

Then: frontmatter with `slug` (equal to the filename stem) and `owners` (every entry a real skill or lens `name`); a `# Title`; a `> Origen:` line with the book's own locators (`M21.4`, `15.6`, `A·H`); and rules in the shape every file here uses — imperative statement, **Why** in one line, **Violated by** with the concrete antipattern, **Checked by** with the schema, tool or lens that catches it. No narrative.

Bidirectionality is the invariant: if a skill is in a file's `owners`, that skill reads the file in its `## Canon`; if it reads it, it is in the owners. Nothing here is copied into a `SKILL.md` — skills cite by path.

Regulatory statements carry their date and locator or they are not written. Generated artifacts speak the book's model aliases, never a provider id.
