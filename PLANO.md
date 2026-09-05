# PLANO — paquete `isa` (Ingeniería de Sistemas Agénticos)

Plano de construcción. **Esto no es contenido: es el contrato entre los agentes que van a construir el paquete en paralelo.** Todo lo que aquí está decidido no se re-decide durante la construcción; lo que aquí no está, se pregunta antes de escribir.

- Origen: `/mnt/c/Users/anton/Documents/Per/Libro Agentes/fuente/libro.md` (8.334 líneas, 38 módulos, anexos A–J, 114 bloques de código). **Solo lectura. No se toca `fuente/` ni `entrega/`.**
- Destino: `/mnt/c/Users/anton/Documents/Per/Libro Agentes/paquete-agentes`
- Ficheros a redactar a mano: **46**. Ficheros extraídos del libro por script: **~53** (`banco/`).
- Convenciones vinculantes: `/home/ancarpi/.claude/plugins/marketplaces/javbrain-claude-marketplace/knowledge/protocols/naming.md`, con la sustitución `jav` → `isa` y la única excepción documentada en §D.1.

---

## A. La tesis del paquete (leer antes de escribir una línea)

El libro no se convierte en documentación: se destila en **criterio cargable**. La prueba de que un fichero de `knowledge/` está bien escrito es que un agente que lo tiene en contexto **decide distinto** — no que sepa más. Cada regla trae su porqué en una línea y su módulo de origen, y nada más.

La columna vertebral son **las doce reglas del arquitecto** (Anexo D, líneas 7984–7997 del libro): son literalmente el índice de criterios que el autor ya escribió. `knowledge/INDEX.md` las cita verbatim y cada una apunta al fichero que la expande. Cobertura verificada en §B.3.

Dos audiencias, un paquete: la persona lee `README.md` + `INDEX.md` + las doce reglas y ya tiene valor sin ejecutar nada; el agente carga el fichero de la regla en el momento de decidir. Ninguna de las dos lee prosa del libro aquí.

---

## B. `knowledge/` — el criterio. 13 ficheros.

Regla de oro, heredada y no negociable: **cada regla vive UNA VEZ aquí; las skills la CITAN, no la repiten.** Un builder que copie el contenido de un fichero de `knowledge/` dentro de un `SKILL.md` ha roto el paquete.

Formato obligatorio de cada fichero: frontmatter `slug` + `owners` (nada más — el resto de claves está prohibido por el estándar), luego `# Título`, luego una línea `> Origen: <localizadores del libro>`, luego las reglas. Cada regla: **enunciado imperativo · porqué en una línea · qué la incumple (el antipatrón concreto) · dónde se comprueba**. Sin prosa de transición. Máximo ~120 líneas por fichero.

### B.1 `protocols/` — cómo funciona la disciplina (8)

| Fichero | Especificación (1–2 líneas) | Origen | `owners` |
|---|---|---|---|
| `INDEX.md` | Tabla de routing keywords → fichero → slug, en el formato exacto del INDEX de javbrain, **más las doce reglas del Anexo D citadas verbatim**, cada una con enlace al fichero que la expande. Es lo que lee una persona y lo que audita `/jav-compact`. | A·D, todo | `isa-criterio` |
| `protocols/autonomy-ladder.md` | La escalera L0–L4: qué es cada peldaño, y **el control obligatorio de cada uno** (L2: no commit; L3: idempotencia+rollback+allow; L4: HITL o maker-checker o step-up, o prohibición). La variable de graduación es el efecto sobre el mundo, nunca la confianza en el modelo. Cierra con: «un L4 sin ninguno de los tres controles no es autonomía graduada, es un incidente pendiente de fecha». | M21.4, A·H, M35.2 | `isa-autonomy-gate`, `isa-tool-manifest`, `isa-scaffold-agent`, `isa-autonomy-drift` |
| `protocols/policy-over-model.md` | «El modelo puede recomendar; la política decide» (cita literal del 26.2 — **no inventar otra formulación**). Qué vive obligatoriamente fuera del LLM (autorización, límite económico, clasificación de datos, rol, geo, HITL) y las cinco decisiones del engine: `allow / deny / require_human / require_dry_run / require_step_up_auth`. Incluye R10: la plataforma debe poder bloquear una herramienta sin redesplegar agentes. | M26.2, M35.2, A·D·2, A·D·10 | `isa-autonomy-gate`, `isa-threat-model`, `isa-autonomy-drift` |
| `protocols/release-gate.md` | **Los seis campos** de una puerta que no es superstición: métrica · conjunto y su versión · nº de casos · pases por caso · umbral · diferencia que se considera real. Las tres fuentes de ruido (muestreo, ejecución, juez), la relación cuadrática caída↔casos, el veredicto **no concluyente**, y versionar el juez como se versiona el agente. Incluye R9 (todo bug → eval, runbook o política). | 15.6, A·G.2, A·D·11, A·D·9 | `isa-eval-gate`, `isa-eval-superstition` |
| `protocols/memory-governance.md` | «No hay memoria sin permisos ni caducidad»: la taxonomía de siete memorias con quién puede escribir y su control crítico; APIs tipadas en vez de `escribir_memoria(texto)`; el **receipt** (quién propuso, qué fuente, qué política, cuándo caduca, cómo se revierte); y los **siete sitios** donde vive un dato personal (store, checkpoints, resúmenes, trazas, auditoría, embeddings, cola). Cierra con R12. | M34.1, M34.5, M34.6, A·D·6, A·D·12 | `isa-memory-governance`, `isa-scaffold-agent` |
| `protocols/ai-act-map.md` | El mapa **obligación → artefacto técnico**: clasificación de riesgo *por caso de uso, nunca por modelo ni servicio*, transparencia (Art. 50), supervisión humana (Art. 14), registro (Art. 12, que es la evidencia jurídica — la traza es técnica y perecedera), gobierno de datos, riesgos, ciberseguridad. Más el suplemento que un auditor mira primero: RGPD (base jurídica por finalidad; el Context Contract *es* la minimización; retención distinta por almacén), DORA (desplaza a NIS2 en financiero; el proveedor de modelos es tercero tecnológico; el reloj de notificación), alfabetización. Estado normativo con fecha explícita (Rgto. 2024/1689 consolidado por 2026/1744, en vigor 27-07-2026). | 16.2, 16.3, 16.4, 16.7 | `isa-aiact-dossier` |
| `protocols/agent-threat-model.md` | La matriz activo → amenaza → control (herramientas, contexto, memoria, trazas, MCP server, agente) con OWASP LLM 2025 y ASI de diciembre 2025 citados **siempre con su año porque se renumeran**. La regla que hace útil un mapeo OWASP: **la tercera columna, el riesgo residual, y alguien lo firma**; lo no mapeado se escribe como no mapeado. Sandboxing y seguridad MCP/A2A. | 16.1, M26.1, M26.3, M26.4 | `isa-threat-model`, `isa-context-leak` |
| `protocols/observability-contract.md` | R7: sin `trace_id`, versión de agente y receipts de herramienta no hay auditoría. Trazas, no logs; métricas por capa; evals online; qué NO entra en una traza (PII, secretos) y por qué la traza no sirve como evidencia regulatoria. | 15.1, M36.1, M36.3, A·D·7 | `isa-scaffold-agent`, `isa-eval-gate` |
| `protocols/production-checklist.md` | Las diez áreas del Anexo F como **puerta previa a producción**, con la regla de uso que el anexo no dice: cada área tiene un owner que firma, y un área sin firma bloquea. Los ítems no se listan aquí — viven en `schemas/production-checklist.yaml`; este fichero es el criterio, no los datos. | A·F | `isa-aiact-dossier`, `isa-scaffold-agent` |

### B.2 `patterns/` — la forma que se implementa (4)

| Fichero | Especificación | Origen | `owners` |
|---|---|---|---|
| `patterns/context-contract.md` | El Context Contract en sus **tres alcances**: por llamada (los ocho campos del 19.1: objetivo, instrucciones, datos permitidos, datos prohibidos, herramientas visibles, salida, límites, fallback), por canal (Conversation Contract, 22.1) y por frontera entre agentes (Handoff Contract, 23.1, con su campo `authority`). No es documentación estética: es una interfaz de seguridad, y sus «datos prohibidos» son la minimización del RGPD implementada. Antipatrón: un nodo que llama a un modelo sin contrato declarado. | 19.1, 22.1, 23.1 | `isa-context-contract`, `isa-context-leak`, `isa-scaffold-agent` |
| `patterns/tool-capability.md` | Una herramienta no entra en producción sin owner, esquema, permisos y tests (R5). Los campos del Tool Capability Manifest y por qué existen; la separación **read / plan / dry-run / commit**; la clave de idempotencia y el `duplicate_behavior`; el rollback como acción compensatoria nombrada; los errores como lenguaje de coordinación (`ToolError` tipado devuelto como `ToolMessage`, nunca excepción cruda). Incluye R8: se comparten capacidades gobernadas, no agentes monolíticos. | M20.1, M20.2, M20.3, M20.4, A·D·5, A·D·8 | `isa-tool-manifest`, `isa-autonomy-drift`, `isa-idempotence` |
| `patterns/backend-reliability.md` | Los cinco mandamientos del backend autónomo (idempotencia · reintento con backoff y DLQ · límites duros de tokens y € · observabilidad con alerta · HITL asíncrono en cola, no bloqueante) más leases, outbox y sagas. R3: nada irreversible sin idempotencia, dry-run o aprobación según su riesgo. | 11.3, M21.1–21.3, A·D·3 | `isa-scaffold-agent`, `isa-idempotence` |
| `patterns/knowledge-governance.md` | R4: un RAG sin evaluación de recuperación no es conocimiento corporativo, es esperanza. La metadata mínima que sí cambia resultados, **permisos en RAG** (un chunk que el sujeto no puede ver es una fuga de contexto, no un problema de relevancia), frescura, procedencia y plan de reindexación; y que la puerta de Recall@k obedece los seis campos de `release-gate.md` como cualquier otra. | 8.3, M24.1–24.3, A·D·4 | `isa-eval-gate`, `isa-context-leak` |

### B.3 Cobertura de las doce reglas (auditoría del plano)

R1→`autonomy-ladder` · R2→`policy-over-model` · R3→`backend-reliability` · R4→`knowledge-governance` · R5→`tool-capability` · R6→`memory-governance` · R7→`observability-contract` · R8→`tool-capability` · R9→`release-gate` · R10→`policy-over-model` · R11→`release-gate` · R12→`memory-governance`. **Doce de doce, sin fichero huérfano y sin regla sin hogar.**

---

## C. `schemas/` — los anexos en papel, convertidos en datos. 11 ficheros.

Decisión de arquitectura: **`knowledge/` solo contiene Markdown; todo lo que una herramienta consume vive en `schemas/`, y solo aquí.** Ninguna skill lleva `references/` propio — así un esquema no puede existir en dos versiones. Los anexos G, H e I dejan de ser plantillas de papel: son estos ficheros.

| Fichero | Especificación | Origen |
|---|---|---|
| `autonomy-levels.yaml` | La matriz del Anexo H como datos: por nivel `L0..L4` → `autonomy`, `examples[]`, `required_controls[]`, `forbidden[]`. Es la tabla que `isa-autonomy-gate` consulta para exigir controles; ninguna skill la reescribe en prosa. | A·H, M21.4 |
| `context-contract.schema.json` | JSON Schema del `ContextContract` del 19.1 (el Pydantic de `src/core/context_contracts.py`). `required`: node, objective, allowed_state_keys, visible_tools, max_input_tokens, max_output_tokens, latency_budget_ms, fallback. | 19.1 |
| `tool-capability.schema.json` | JSON Schema del manifiesto del 20.1. `required` incluye `owner`, `risk_tier` (enum ligado a `autonomy-levels.yaml`), `idempotency.key`, `idempotency.duplicate_behavior` y `rollback`. Un manifiesto sin rollback ni clave de idempotencia **no valida**. | M20.1 |
| `eval-card.schema.json` | Eval Card del A·G.2 **ampliada con los seis campos del 15.6**: `n_cases`, `passes_per_case` y `min_detectable_effect` son `required`. Este `required` es el mecanismo por el que `isa-eval-gate` se niega: no es una decisión del modelo, es validación. | 15.6, A·G.2 |
| `agent-package.schema.json` | JSON Schema del `agent.yaml` del 32.3: id, tenant, version, owner, runtime, entrypoint, risk_tier, channels, models, tools_allowed, memory_scopes, evals.release_gate, human_in_the_loop.required_for, slo. | M32.3 |
| `ai-act-obligations.yaml` | Obligación → artículo → artefacto técnico exigido → módulo del libro que lo implementa → dónde se guarda la evidencia. Incluye las filas de RGPD y DORA del 16.4. Es la entrada de `isa-aiact-dossier`. | 16.3, 16.4, 16.7 |
| `production-checklist.yaml` | Las diez áreas del Anexo F con `id` por ítem, `owner_role` y `blocking: true|false`, para que se pueda marcar y para que un script cuente lo que falta. | A·F |
| `adversarial-cases.yaml` | Los doce casos del Anexo I como corpus: `id`, `surface` (chat, RAG, MCP, skill, batch…), `input`, `expected`, `owasp[]`, `autonomy_level`. Consumible como semilla de red team y como dataset de la puerta. | A·I |
| `threat-model.yaml` | La matriz del 26.1 como datos: `asset` → `threats[]` → `controls[]` → `owasp[]`. Entrada de `isa-threat-model` para fanout por activo. | M26.1, 16.1 |
| `adr.template.md` | El ADR del A·G.1, tal cual, como plantilla que un humano copia (`.template.md` por el estándar de nombres). | A·G.1 |
| `runbook.template.md` | El runbook corto del A·G.3, igual. | A·G.3 |

Regla de datos: los nombres de campo se mantienen **en inglés y verbatim del libro** (`risk_tier`, `idempotency`, `release_gate`, `human_in_the_loop`). No se traducen, no se «mejoran».

---

## D. `skills/` — 8 skills, una por trabajo que un ingeniero repite.

### D.1 Nombrado y frontmatter

Paquete = **plugin propio `isa`** publicado en el marketplace del autor (no ficheros sueltos dentro de `javbrain`). Se aplica `protocols/naming.md` íntegro con `jav` → `isa`:

- Directorio de skill = `name` del frontmatter, kebab, 2–5 segmentos: `^isa(?:-[a-z0-9]+){1,4}$`.
- Frontmatter de skill, **ocho claves en este orden**: `name · description · user-invocable · allowed-tools · argument-hint · effort · model · category`. `argument-hint` obligatoria (puede ser `""`). Prohibidas: `license`, `version`, `metadata`, `author`, `compatibility`. `allowed-tools` en lista inline separada por comas, **nunca lista YAML de bloque**.
- `description`: escalar **entre comillas dobles**, empieza en mayúscula, 120–600 caracteres (objetivo 300–450), máximo 8 frases gatillo, **la primera cita su propio slash command**, y las gatillo van en español y en inglés verbatim como las teclea un humano. Sin apóstrofos dentro de una frase entre comillas simples.
- `category` del enum cerrado: `domain` para las siete de trabajo, `meta` para `isa-criterio`.
- **Excepción documentada (la única del paquete):** los agentes van en `agents/isa/` con stem `isa-<rol>.md`, no `isa-isa-<rol>.md`. En un plugin de una sola familia el prefijo *es* el segmento de familia, y la correspondencia carpeta↔nombre se mantiene. Se declara en el README y en la fila de `exceptions.json` si el linter del autor se apunta alguna vez a este árbol.

### D.2 Cómo cita una skill a `knowledge/` (esto es lo que evita el paquete incoherente)

1. Cada `SKILL.md` abre con una sección **`## Canon`** que lista los ficheros exactos que debe `Read` antes de actuar, por **ruta relativa a la raíz del plugin, entre backticks** — `knowledge/protocols/autonomy-ladder.md` —, resuelta en ejecución como `${CLAUDE_PLUGIN_ROOT}/knowledge/...`. Nunca por nombre de regla suelto, nunca por número de módulo, nunca por copia.
2. La sección termina con la frase, literal en todas las skills: **«Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.»** Es el patrón «Step 1 — load the canon» que el autor ya tiene probado en `jav-review-contracts`.
3. Los agentes reciben la raíz del plugin en el prompt de despacho y **si no la reciben, lo dicen y paran** — no revisan de memoria. Verbatim el comportamiento de `jav-review-contracts`.
4. Bidireccionalidad: si una skill aparece en `owners` de un fichero de `knowledge/`, esa skill lo `Read` de verdad; y si lo lee, está en sus `owners`. Es lo que `/jav-compact` audita.
5. El libro se cita **por localizador, nunca por cita textual**: `M21.4`, `15.6`, `A·H`, `A·J.5` — la notación propia del libro. La **única** prosa citada literalmente en todo el paquete son las doce reglas del Anexo D en `INDEX.md` y la frase «El modelo puede recomendar; la política decide» del 26.2. Todo lo demás se destila. Esto es a la vez higiene de ingeniería y protección del libro: el paquete es la herramienta, no el sustituto.

### D.3 Las ocho skills

| Skill | Trabajo que hace | `model`/`effort` | Canon que carga | Entregable |
|---|---|---|---|---|
| `isa-criterio` | Consulta: «¿qué criterio aplica a X?». Enruta sobre `INDEX.md` y devuelve la regla con su localizador del libro. Es la mitad «aprender» del encargo y la puerta de entrada del paquete. Gatillos: `/isa-criterio`, «qué dice el libro sobre», «cuál es el criterio de», "what is the rule for". | `haiku`/`low`, `meta` | `knowledge/INDEX.md` y el fichero que resuelva | la regla + localizador, sin inventar |
| `isa-scaffold-agent` | Levanta un agente LangGraph ya gobernado: checkpointer, alias del gateway (nunca id de proveedor), trazas con `trace_id` y versión, límites de coste y pasos, contrato de contexto por nodo y `agent.yaml` validado. Se niega a generar un agente con herramientas de efecto sin nivel de autonomía asignado. | `sonnet`/`medium` | `autonomy-ladder`, `context-contract`, `backend-reliability`, `observability-contract`, `memory-governance`, `production-checklist` | árbol de código + `agent.yaml` |
| `isa-context-contract` | Escribe o audita el contrato de una llamada, un canal o una frontera. Exige los ocho campos y **rechaza «datos permitidos» sin su «datos prohibidos»**. | `sonnet`/`medium` | `patterns/context-contract.md`, `schemas/context-contract.schema.json` | contrato validado contra el esquema |
| `isa-tool-manifest` | Escribe el Tool Capability Manifest de una herramienta nueva: `risk_tier`, precondiciones, efectos, clave de idempotencia, aprobadores, timeouts, auditoría y rollback. Obliga a separar dry-run de commit cuando el tier lo exige. | `sonnet`/`medium` | `patterns/tool-capability.md`, `autonomy-ladder`, `schemas/tool-capability.schema.json` | `<tool>.capability.yaml` que valida |
| `isa-autonomy-gate` | Asigna L0–L4 a una acción o a un agente y **exige los controles de ese nivel**: devuelve veredicto, y bloquea si un L3 no tiene idempotencia y rollback o un L4 no tiene HITL, maker-checker o step-up. Entrada = especificación (no diff: eso es la lente). | `sonnet`/`high` | `autonomy-ladder`, `policy-over-model`, `schemas/autonomy-levels.yaml` | nivel + controles exigidos + veredicto |
| `isa-eval-gate` | Escribe la puerta de release con los seis campos y **se niega si falta tamaño de muestra o pases por caso** — la negativa la produce el `required` del esquema, no el criterio del modelo. Calcula qué caída puede detectar la muestra propuesta y lo dice antes de fijar el umbral. | `sonnet`/`medium` | `release-gate`, `knowledge-governance`, `schemas/eval-card.schema.json` | Eval Card que valida + tamaño mínimo |
| `isa-threat-model` | El threat model del M26 sobre un sistema concreto: recorre `threat-model.yaml` activo por activo, mapea a OWASP LLM 2025 / ASI 2025 **con año**, y produce la tercera columna — el riesgo residual y quién lo firma. Siembra casos de `adversarial-cases.yaml`. | `opus`/`high` | `agent-threat-model`, `policy-over-model`, `schemas/threat-model.yaml`, `schemas/adversarial-cases.yaml` | matriz de 3 columnas + casos de red team |
| `isa-aiact-dossier` | Mapea un sistema a sus obligaciones y **a los artefactos técnicos que exige**, distinguiendo papel (proveedor / responsable del despliegue) y clasificando por caso de uso. Cierra con lo que falta y con el Anexo F contado. | `sonnet`/`high` | `ai-act-map`, `production-checklist`, `schemas/ai-act-obligations.yaml`, `schemas/production-checklist.yaml` | dossier + `clasificacion-ia.yaml` + huecos |

Lo que **no** es una skill, deliberadamente: memoria y RAG. Su criterio se carga desde `isa-scaffold-agent` y se audita con lentes; una skill más sería un fichero que nadie invoca.

---

## E. `agents/isa/` — 5 lentes de revisión.

Patrón exacto de `agents/sec/*` y `agents/review/*` del autor: frontmatter `name · description · tools · model · effort`; `tools: Read, Grep, Glob` en todas (**una lente no modifica ficheros, nunca**); cargan el canon del prompt de despacho y paran si no lo tienen; salida en **una única tabla de hallazgos ordenada por severidad** más la línea `Reviewed: <ficheros realmente leídos>`; `No findings in scope.` si no hay nada, y **jamás inventar hallazgos para llenar la tabla**. Cada una declara su `## Out of scope` nombrando a sus hermanas — así se lanzan en paralelo sin solaparse.

| Lente | Único lente | Canon | `model`/`effort` |
|---|---|---|---|
| `isa-autonomy-drift.md` | Herramientas y nodos **actuando por encima de su nivel autorizado**: efecto irreversible sin HITL/maker-checker/step-up, commit alcanzable sin dry-run previo, `risk_tier` declarado que no cuadra con lo que el código hace, agente cuyo `tools_allowed` excede su `risk_tier`. | `autonomy-ladder`, `tool-capability`, `policy-over-model` | `sonnet`/`medium` |
| `isa-context-leak.md` | **Nodos sin contrato de contexto** y fugas: llamada al modelo sin contrato declarado, dato prohibido que llega a la llamada, instrucciones y datos en el mismo canal, chunk de RAG servido sin comprobar el permiso del sujeto, PII en trazas o en checkpoints. | `context-contract`, `agent-threat-model`, `knowledge-governance` | `sonnet`/`medium` |
| `isa-eval-superstition.md` | **Umbrales sin tamaño de muestra**: umbral sin `n` ni pases por caso, métrica de un solo pase reportada como medición, cifra sin intervalo, juez LLM sin calibrar o sin versionar, puerta cuyo conjunto no puede detectar la caída que declara. Trabajo de checklist puro. | `release-gate` | `haiku`/`low` |
| `isa-memory-governance.md` | **Memoria escrita sin owner, TTL o permiso**: `escribir_memoria(texto)` genérica, escritura sin procedencia ni sensibilidad, memoria colectiva publicada sin revisión, borrado que solo toca el store y olvida checkpoints, resúmenes, trazas y embeddings. | `memory-governance` | `sonnet`/`medium` |
| `isa-idempotence.md` | Efectos externos sin red: acción irreversible sin clave de idempotencia, reintento que duplica efecto, ausencia de outbox o de DLQ, saga sin compensación, worker sin lease, límite de coste o de pasos inexistente. | `backend-reliability`, `tool-capability` | `sonnet`/`medium` |

Cinco lentes = cinco dimensiones independientes = un fanout en paralelo, que es lo que pide `§6` del CLAUDE.md del autor. Familia de cinco miembros, por encima del mínimo de tres.

---

## F. `banco/` — el repositorio de referencia.

### F.1 El principio de mapeo (cuatro reglas, y cierran todos los casos)

1. **El basename declarado se preserva verbatim; solo se decide el directorio.** `agente_backoffice.py` no se renombra a `agente.py` aunque quede redundante: el libro impreso tiene que seguir siendo copiable línea a línea.
2. **Estructura impuesta por el Ejercicio 0.1**, literal: `src/{core,agents,rag,channels,evals}/`, y `get_model()` en **`src/core/models.py` — esa ruta exacta**, porque de ella tira el resto del libro. Los cinco canales del 18.3 («un cerebro, cinco pieles») son los cinco subdirectorios de `src/channels/`.
3. **Bloques consecutivos de un mismo fichero entregado se concatenan en orden del libro.** No son ficheros distintos: `nano_agent.py` son sus tres piezas del 3.3 (L726-792 + L801-863 + L869-944); `supervisor.py` son sus cinco bloques del 9.2; `db/schema.sql` son cuatro (7.6 base + mod-97 IMMUTABLE + roles + `registro_ia` del 16.6, que el propio libro dice que «va en el schema.sql del 7.6»). Los parches de M17 y M18 («se pega al final del servidor.py del 12.5», «justo encima de main()») se aplican al fichero destino con un marcador de comentario que nombra su módulo.
4. **Un bloque sin nombre solo obtiene fichero si (a) el libro le da ruta en prosa, (b) es adenda de un fichero declarado, o (c) una skill, un esquema o una lente lo referencian.** Todo lo demás es ilustrativo y **se queda en el libro**. Esta es la regla que evita que el repo se llene de fragmentos de veinte líneas que nadie ejecuta.

### F.2 Mapeo: nombre declarado → ruta real

| Declarado en el libro | Ruta en el repo | Nota |
|---|---|---|
| `config.yaml` (0.5) | `gateway/config.yaml` | es la config del gateway, no de la app; `os.environ/` únicamente |
| `.env.gateway` (0.5) | `gateway/.env.gateway.example` | valores vacíos, **nunca un secreto** |
| *(sin nombre, 0.4 L228-253)* | `src/core/models.py` | **ruta obligada por el Ejercicio 0.1** |
| *(sin nombre, 0.5 L418-440)* | `src/core/models_local.py` | variante sin gateway; el resto del repo no se entera |
| `nano_agent.py` (3.3) | `src/agents/nano_agent.py` | tres piezas concatenadas |
| *(dicts del core, 3.3→9.2)* | `src/core/banco.py` | el libro nombra esta ruta en el 3.3 |
| `herramientas.py` (4.1) | `src/agents/backoffice/herramientas.py` | |
| `agente_backoffice.py` (4.3) | `src/agents/backoffice/agente_backoffice.py` | |
| `grafo_conciliacion.py` (6.3, referenciado) | `src/agents/conciliacion/grafo_conciliacion.py` | **stub de ejercicio**: el estado del 5.1 + TODO al Ejercicio 5.1. Marcado como andamio, no como código del libro |
| `canal_chat.py` (6.3) | `src/channels/chat/canal_chat.py` | |
| `fanout_nocturno.py` (6.4) | `src/agents/conciliacion/fanout_nocturno.py` | |
| `schema.sql` (7.6) | `db/schema.sql` | cuatro bloques |
| *(PGEngine, 7.4)* | `src/rag/indexar.py` | driver explícito `postgresql+psycopg://` |
| `src/rag/08_hibrida.sql` | `src/rag/08_hibrida.sql` | migración léxica, verbatim |
| `src/rag/hibrida.sql` | `src/rag/hibrida.sql` | la consulta de las dos ramas |
| `src/rag/hibrida.py` | `src/rag/hibrida.py` | |
| `src/rag/rerank.py` | `src/rag/rerank.py` | |
| `supervisor.py` (9.2) | `src/agents/supervisor/supervisor.py` | cinco bloques |
| `mcp_core.py` (10.2) | `src/core/mcp_core.py` | expone las tablas del core: es core, no canal |
| `cliente_core.py` (10.2) | `src/agents/cliente_core.py` | |
| *(allow-list sha256, 10.2)* | `src/agents/allowlist_mcp.json` | el fichero que el propio 10.2 describe |
| `batch_nocturno.py` (11.5 + 17.2) | `src/channels/backend/batch_nocturno.py` | el quinto canal; incluye `informe()` del 11.5 y la adenda de K8s |
| `servidor.py` (12.5 + 17.2) | `src/channels/chat/servidor.py` | incluye sonda, cola y apagado ordenado |
| `webhook_slack.py` (12.6) | `src/channels/slack/webhook_slack.py` | |
| `grafo_voz.py` (13.4) | `src/agents/voz/grafo_voz.py` | el cerebro |
| `agente_voz.py` (13.4) | `src/channels/voz/agente_voz.py` | la piel |
| `cara.py` (14.2) | `src/channels/avatar/cara.py` | |
| `cumplimiento.py` (16.5) | `src/core/cumplimiento.py` | compartido por las cinco superficies |
| *(las costuras del 16.5 y 18.3)* | `COSTURAS.md` | mapa «qué fragmento parchea qué fichero»; es instrucción, no código |
| `compliance/clasificacion-ia.yaml` | `compliance/clasificacion-ia.yaml` | verbatim |
| `tests/test_clasificacion.py` | `tests/test_clasificacion.py` | verbatim |
| `despliegue-chat.yaml` (17.2) | `deploy/despliegue-chat.yaml` | |
| `autoescalado.yaml` (17.2) | `deploy/autoescalado.yaml` | |
| *(apps/v1, 27.3)* | `deploy/runtime-prolongado.yaml` | |
| `identidad.py` (18.3) | `src/core/identidad.py` | |
| `src/core/context_contracts.py` (19.1) | `src/core/context_contracts.py` | verbatim |
| `config/model_routing.yaml` (19.2) | `config/model_routing.yaml` | verbatim |
| `tools/bloquear_tarjeta.capability.yaml` (20.1) | `tools/bloquear_tarjeta.capability.yaml` | verbatim; valida contra `schemas/tool-capability.schema.json` |
| *(dry-run/commit, 20.2)* | `src/agents/cards_disputes/herramientas.py` | el `entrypoint` que declara `agent.yaml` |
| *(ToolError 20.3, Handoff 23.1, HumanHandoffPacket 22.3)* | `src/core/contratos.py` | el vocabulario tipado que cruza fronteras |
| *(estados de job 21.2, `claim_next_job` 21.3)* | `src/core/trabajos.py` | |
| *(policy engine 26.2 + forma de llamada 35.2)* | `src/core/politica.py` | |
| *(MemoryRecord 34.1 + tres tools 34.5)* | `src/core/memoria.py` | |
| *(trayectoria 25.3)* | `src/evals/trayectoria.py` | |
| *(nombrado por `aceptacion.py`)* | `src/evals/medidas.py` | el 31.2 lo nombra explícitamente |
| `.github/workflows/agent-evals.yml` (25.5) | `.github/workflows/agent-evals.yml` | marcado como **extracto conceptual**, igual que el libro |
| `aceptacion.py` (31.2) | `aceptacion.py` | raíz: es la puerta del capstone |
| `agent.yaml` (32.3) | `catalogo/cards-disputes/agent.yaml` | su `entrypoint` obliga a que exista `src/agents/cards_disputes/` |
| `plataforma/runtime.py` (37.2) | `plataforma/runtime.py` | verbatim, con la política y el HITL del 37.2 en el mismo `wrap_tool_call` |
| *(Ejercicio 0.1)* | `smoke_test.py` | dos alias, latencia y tokens, Postgres y traza |

Más, a mano: `README.md` (qué es, qué módulo entrega cada fichero, cómo arrancar), `pyproject.toml` (`uv`, como el libro), `conftest.py` (el `.env` que pytest no lee solo), `docker-compose.yml` (el Postgres con pgvector que el árbol necesita), `contratos/triage_sepa.contract.yaml` y `evals/capstone_gate.eval.yaml` (los dos artefactos del libro traducidos a datos, 19.1 y 18.4), `MAPEO.md` (**generado**, no escrito) y `.env.example` (**generado** por `tools/generar_env/` desde el bloque `.env` del 0.4).

### F.3 Extracción

**Con script, nunca a mano.** El mapeo vive una sola vez y como datos, en `tools/extraer_banco/mapeo.yaml`: por entrada, `bloques: [Lini-Lfin, ...]`, `destino`, `modo: verbatim|concat|patch|stub`, `modulo`. `extraer_banco.py` lo aplica sobre `libro.md`, escribe el árbol, genera `banco/MAPEO.md` y **falla si un rango ya no empieza donde decía** — el libro sigue vivo en `fuente/`, así que la extracción tiene que romperse en voz alta cuando las líneas se muevan, en vez de escribir basura. Solo stdlib.

---

## G. Raíz del paquete y `tools/`

| Fichero | Especificación |
|---|---|
| `README.md` | Qué es y para quién (las dos audiencias del encargo, literal). Instalación como plugin del marketplace. Las cuatro partes en una línea cada una. **La tabla de las 8 skills con su frase gatillo y la de las 5 lentes.** La escalera L0–L4 inline, porque es la tabla más usada y hace útil el README solo. Cómo se cita `knowledge/` (§D.2, resumido en tres líneas). La excepción de nombrado de §D.1. Cómo añadir una regla (una regla, un fichero, una fila en `INDEX.md`). Y la frase que hay que escribir sin adornos: **esto es la herramienta, no el sustituto del libro** + enlace a Amazon. |
| `LICENSE` | MIT, `Copyright (c) 2026 Antonio Carbonell`. Cubre paquete y `banco/`. |
| `CHANGELOG.md` | Sección `## 0.1.0` con el contenido inicial. Lo exige la regla de manifiestos del estándar. |
| `plugin.json` | `name: "isa"`, `version: "0.1.0"`, descripción y autor. La fila de `marketplace.json` se añade en el repo del marketplace, **no aquí**. |
| `tools/extraer_banco/extraer_banco.py` | Extractor de §F.3. stdlib. |
| `tools/extraer_banco/mapeo.yaml` | El mapeo de §F.2 como datos. **Única fuente del mapeo.** |
| `tools/extraer_banco/API.md` | Qué hace, cómo se invoca, `## Consumers`. |
| `tools/isa_validate/isa_validate.py` | Valida cualquier `*.capability.yaml`, `agent.yaml`, eval card o contrato de un repo contra `schemas/`. Exit ≠ 0 si falta un campo `required`. Es el mecanismo real de la negativa de `isa-eval-gate` y `isa-tool-manifest`. stdlib. |
| `tools/isa_validate/API.md` | Ídem, con sus consumidores. |

---

## H. Decisiones transversales (las que romperían el paquete si cada builder eligiera la suya)

1. **Prefijo e identidad.** Plugin `isa`; todo artefacto lleva `isa-`; `naming.md` del autor íntegro con `jav`→`isa`; única excepción, los stems de `agents/isa/` (§D.1).
2. **Cita de knowledge.** Ruta relativa a la raíz del plugin, entre backticks, en una sección `## Canon` al principio de cada skill; `${CLAUDE_PLUGIN_ROOT}` en ejecución; los agentes paran si no reciben la raíz. Nunca nombre de regla suelto. Nunca copia. (§D.2)
3. **Cita del libro.** Localizadores propios del libro (`M21.4`, `15.6`, `A·H`), en una línea `> Origen:` bajo el título. Prosa citada literalmente: **solo** las doce reglas del A·D y la frase del 26.2. Todo lo demás destilado.
4. **Idioma.** `description`, prosa de `knowledge/` y campos de `schemas/` en inglés (convención del marketplace y lo que lee el router); frases gatillo en español **y** inglés; `banco/` en español y verbatim del libro, incluidos los comentarios, porque tiene que coincidir con la página impresa. `README.md` y `PLANO.md` en español.
5. **Markdown vs datos.** `knowledge/` solo `.md`; todo lo que consume una herramienta, solo en `schemas/`; ninguna skill lleva `references/`. Un esquema no puede existir dos veces.
6. **Las negativas son validación, no criterio del modelo.** `isa-eval-gate` se niega porque `n_cases` es `required` en el esquema y `isa_validate.py` sale con error; no porque el modelo se acuerde. Lo mismo con el manifiesto sin rollback. Esta es la diferencia entre una regla y una recomendación.
7. **Alias, jamás id de proveedor.** Todo lo generado habla los alias del libro (`agente-rapido`, `agente-equilibrado`, `agente-listo`, `emb-multilingue`, `rerank-multilingue`), nunca `claude-*` ni `gpt-*`. Coherente con el 0.5 y con el `stack.md` del autor.
8. **Secretos.** Cero valores reales. Solo `os.environ/` y ficheros `.example` vacíos.
9. **Licencia.** MIT, todo público, un solo `LICENSE` en la raíz. Aviso al autor: la **prosa** del libro sigue siendo suya y con derechos; que `knowledge/` sea destilado y no citado es también lo que mantiene esa frontera limpia — la regla 3 de esta lista no es solo estilo.
10. **Fechas y normativa.** Cualquier afirmación regulatoria lleva su fecha y su localizador (`Rgto. (UE) 2024/1689` consolidado por `2026/1744`, en vigor 27-07-2026; OWASP LLM **2025**, ASI **diciembre 2025**). Sin fecha, no se escribe.
11. **Frontera con `javbrain`.** El paquete no redefine nada que ya viva en `javbrain/knowledge/` (coste, orquestación, nombrado, observabilidad de Langfuse): lo cita como plugin hermano cuando hace falta. Lo de aquí es el criterio del libro; lo de allí, la operación de la casa.
12. **Anti-fragmentación.** Contenido nuevo de menos de ~30 líneas sustantivas se dobla en su fichero padre; no se crea fichero ni carpeta. Es la razón de que Conversation Contract y Handoff Contract vivan dentro de `context-contract.md` y de que no exista una skill de memoria.

---

## I. Orden de construcción (para el fanout, sin colisiones)

Cuatro lotes; dentro de cada lote, todo en paralelo. **Nadie escribe fuera de su lote.**

- **Lote 1 (bloqueante, uno solo):** `knowledge/` completo, 13 ficheros. Es el canon; nada puede citarlo antes de que exista.
- **Lote 2 (en paralelo con el 3):** `schemas/`, 11 ficheros — transcripción mecánica de los anexos, no requiere juicio.
- **Lote 3:** `skills/` (8) y `agents/isa/` (5), en paralelo, cada uno citando el canon del lote 1 por ruta. Un builder por familia.
- **Lote 4:** `tools/` (5) + `banco/` por extracción + raíz (4). `MAPEO.md` y el árbol de `banco/` los produce el script, no un agente.

Verificación de cierre, y sin ella el paquete no está hecho: (a) `isa_validate.py` valida en verde un ejemplo de cada uno de sus cuatro modos --- `banco/contratos/triage_sepa.contract.yaml`, `banco/evals/capstone_gate.eval.yaml`, `banco/tools/bloquear_tarjeta.capability.yaml` y `banco/catalogo/cards-disputes/agent.yaml` --- y sale con código 1 y el campo señalado sobre los dos negativos de §227, una capacidad sin `idempotency.key` y una eval card sin `n_cases`; (b) `extraer_banco.py` corre limpio y `MAPEO.md` cuadra con §F.2; (c) el `naming_lint.py` del autor, apuntado a este árbol, sale sin errores salvo la excepción de §D.1; (d) cada `owners` de `knowledge/` resuelve a una skill o lente real **y** esa skill lo cita en su `## Canon`; (e) ninguna regla de `knowledge/` aparece copiada dentro de un `SKILL.md` — un grep de las frases clave lo prueba.
