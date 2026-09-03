# `isa` --- el paquete de «Ingeniería de Sistemas Agénticos»

El paquete de acompañamiento de **«Ingeniería de Sistemas Agénticos --- Manual completo de LangChain y LangGraph»**, de Antonio Carbonell (primera edición, septiembre de 2026). Presentado en el 0.1 del libro, con las versiones exactas en el 0.4 y su entrada en el Anexo C.

**Esto es la herramienta, no el sustituto del libro.** Aquí está el código y está el criterio en forma comprobable; lo que no está --- ni puede estar --- es el razonamiento que lleva de un problema a esa decisión, que es lo que ocupa el libro entero. Si has llegado sin el libro, te falta la parte que importa.

Y una honestidad de partida: esto es la **implementación de referencia extraída del libro**, no un producto terminado. Corre lo que el libro deja corriendo, y los fragmentos están marcados como fragmentos.

---

## Las cuatro partes

| Parte | Qué es |
|---|---|
| `banco-meridiano/` | El código de Meridiano extraído del libro por un script, en el árbol del Ejercicio 0.1. Qué corre, qué corre con sus hermanos en el `PYTHONPATH` y qué es fragmento a propósito: su propio `README.md` lo dice fichero a fichero. |
| `knowledge/` | El criterio. Trece ficheros: `INDEX.md`, que es la puerta de entrada, y **doce reglas, una por fichero**, cada una con su porqué en una línea y su localizador del libro. Son las doce reglas del Anexo D expandidas a forma comprobable. Nada se duplica entre ellas. |
| `skills/`, `agents/isa/` | Ocho skills que citan `knowledge/` por ruta, y cinco lentes de revisión que auditan un sistema agéntico contra esas reglas. |
| `schemas/` | Los datos que consume una herramienta: once esquemas y plantillas --- niveles de autonomía, contratos de contexto, manifiestos de capacidad, eval cards, obligaciones del AI Act, threat model, casos adversarios, checklist de producción, ADR y runbook. |

Más dos piezas: `tools/extraer_meridiano/`, el extractor que produce `banco-meridiano/` desde `libro.md` y que **falla en voz alta** cuando las líneas del libro se mueven en vez de escribir basura; y `tools/isa_validate/`, el validador sin dependencias que decide si un artefacto cumple su esquema --- es lo que hace que las negativas de las skills sean validación y no opinión del modelo.

Y **`ERRATA.md`**, que es lo que el 0.4 del libro promete: las correcciones posteriores al cierre de agosto de 2026, fechadas y diciendo qué versión de qué librería provocó cada una. Antes de dar por roto un bloque de código del manual, es el primer sitio donde mirar.

## Las ocho skills

| Skill | Trabajo que hace |
|---|---|
| `isa-criterio` | La puerta de entrada: «¿qué criterio aplica a X?». Enruta sobre `INDEX.md` y devuelve la regla con su localizador del libro. |
| `isa-scaffold-agent` | Levanta un agente LangGraph ya gobernado: checkpointer, alias del gateway, trazas, límites, contrato de contexto por nodo y `agent.yaml` validado. |
| `isa-context-contract` | Escribe o audita el contrato de una llamada, un canal o una frontera. Rechaza «datos permitidos» sin su «datos prohibidos». |
| `isa-tool-manifest` | El Tool Capability Manifest de una herramienta nueva: riesgo, efectos, idempotencia, aprobadores, auditoría y rollback. |
| `isa-autonomy-gate` | Asigna L0–L4 a una acción o a un agente y exige los controles de ese nivel. Bloquea si faltan. |
| `isa-eval-gate` | La puerta de release con sus seis campos. Se niega si falta tamaño de muestra o pases por caso. |
| `isa-threat-model` | El threat model activo por activo, mapeado a OWASP con su año, y la tercera columna: riesgo residual y quién lo firma. |
| `isa-aiact-dossier` | Mapea un sistema a sus obligaciones y a los artefactos técnicos que exigen, distinguiendo papel y clasificando por caso de uso. |

## Las cinco lentes

Cinco dimensiones independientes, pensadas para lanzarse en paralelo sobre un mismo diff. Ninguna modifica ficheros.

| Lente | Único lente |
|---|---|
| `isa-autonomy-drift` | Herramientas y nodos actuando por encima de su nivel autorizado. |
| `isa-context-leak` | Llamadas al modelo sin contrato de contexto, y fugas de dato prohibido. |
| `isa-eval-superstition` | Umbrales sin tamaño de muestra ni pases por caso. |
| `isa-idempotence` | Efectos externos sin red: sin clave de idempotencia, sin outbox, sin compensación. |
| `isa-memory-governance` | Memoria escrita sin owner, caducidad o permiso. |

## Cómo se cita `knowledge/`

Tres reglas, y son las que evitan un paquete incoherente:

1. Cada `SKILL.md` abre con una sección `## Canon` que lista, **por ruta relativa entre backticks**, los ficheros que debe leer antes de actuar. Nunca por nombre de regla suelto, nunca por copia.
2. Esa sección cierra siempre con la misma frase: «Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.»
3. Bidireccionalidad: si una skill está en los `owners` de un fichero de `knowledge/`, esa skill lo lee de verdad; y si lo lee, está en sus `owners`.

El libro se cita **por localizador** (`M21.4`, `15.6`, `A·H`), nunca textualmente. La única prosa citada literalmente en todo el paquete son las doce reglas del Anexo D en `INDEX.md` y una frase del 26.2. Todo lo demás está destilado --- que es a la vez higiene de ingeniería y la frontera que protege la prosa del libro.

## Añadir una regla

Una regla, un fichero, una fila en `INDEX.md`. `¿Cómo funciona la disciplina?` → `protocols/`. `¿Es una forma que se implementa en código?` → `patterns/`. `¿Es un dato que consume una herramienta?` → `schemas/`, no `knowledge/`. Por debajo de unas treinta líneas sustantivas, dentro de su fichero padre. El detalle está en `knowledge/INDEX.md`.

## Nombrado

Todo artefacto lleva el prefijo `isa-`. Una excepción, la única del paquete: las lentes viven en `agents/isa/` con stem `isa-<rol>.md`, no `isa-isa-<rol>.md` --- en un plugin de una sola familia el prefijo *es* el segmento de familia.

## Estado

Este README es la versión mínima; la completa que especifica `PLANO.md` --- las frases gatillo de cada skill y la escalera L0–L4 en línea --- está pendiente, igual que `CHANGELOG.md` y `plugin.json`. `tools/isa_validate/` ya existe: es el mecanismo real --- y no el criterio del modelo --- de las negativas que citan cuatro skills y cuatro ficheros de `knowledge/`. `PLANO.md` es el contrato de construcción, no documentación de usuario.

Las **erratas y actualizaciones** del libro se publican aquí.

## Licencia

MIT --- `Copyright (c) 2026 Antonio Carbonell`. Cubre el paquete entero, `banco-meridiano/` incluido.

La licencia cubre el **código**. La **prosa** del libro sigue siendo del autor y con todos sus derechos: por eso aquí solo hay código, esquemas y criterio destilado, y ni una página citada.
