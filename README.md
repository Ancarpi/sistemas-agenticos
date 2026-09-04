# Ingeniería de Sistemas Agénticos --- el paquete del libro

[![promesas](https://github.com/Ancarpi/sistemas-agenticos/actions/workflows/promesas.yml/badge.svg)](https://github.com/Ancarpi/sistemas-agenticos/actions/workflows/promesas.yml)

El paquete de acompañamiento de **«Ingeniería de Sistemas Agénticos --- Manual completo de LangChain y LangGraph»**, de Antonio Carbonell (primera edición, septiembre de 2026). Presentado en el 0.1 del libro, con las versiones exactas en el 0.4 y su entrada en el Anexo C.

**Qué es.** Tres cosas en un árbol: el **código** del caso único del libro --- un banco ficticio con cinco superficies sobre un solo cerebro ---, extraído byte a byte del manual por un script que falla en voz alta si el libro se mueve; el **criterio** del libro en forma comprobable --- doce reglas, ocho skills y cinco lentes de revisión para Claude Code ---; y el **mecanismo** que convierte ese criterio en verificación y no en opinión: once esquemas y un validador sin dependencias.

**Qué hago con ello.** `QUICKSTART.md` te lleva de `git clone` a algo corriendo en tres escalones --- el primero sin montar absolutamente nada. Después, tres usos: seguir el libro con el código al lado (`banco/MAPEO.md` dice de qué página salió cada fichero); auditar tu propio sistema agéntico con las skills, las lentes y el validador; y consultar `ERRATA.md` antes de dar por roto un bloque del manual.

**En qué se diferencia de un repo de ejemplos.** Un repo de ejemplos demuestra que algo puede funcionar; este paquete empaqueta el criterio para decidir si lo tuyo puede salir a producción. Las negativas aquí no son memoria de un modelo: son un script saliendo con código distinto de cero y nombrando el campo. Cada regla de `knowledge/` declara quién la comprueba, el CI de este repo comprueba las promesas de este README --- incluidos dos artefactos que **deben** fallar ---, y lo que no corre está dicho de frente en vez de disimulado.

**Esto es la herramienta, no el sustituto del libro.** Lo que no está --- ni puede estar --- es el razonamiento que lleva de un problema a cada decisión, que es lo que ocupa el libro entero. Y una honestidad de partida: esto es la implementación de referencia extraída del libro, no un producto terminado. Corre lo que el libro deja corriendo, y los fragmentos están marcados como fragmentos.

## El árbol

```
.
├── QUICKSTART.md            de git clone a algo corriendo, en tres escalones
├── ERRATA.md                correcciones fechadas del libro: qué versión de qué librería rompió qué
├── CONTRIBUTING.md          los dos carriles: errata del libro (issue) o problema del paquete (PR)
├── banco/         el código del libro en el árbol del Ejercicio 0.1 — NO editar: se regenera
│   ├── README.md            el arranque de los procesos que corren; la procedencia de todos, en MAPEO.md
│   ├── MAPEO.md             generado: qué módulo del libro entrega cada fichero, con líneas exactas
│   └── COSTURAS.md          generado: los fragmentos que el libro deja para pegar a mano
├── knowledge/               el criterio: INDEX.md + doce reglas, una por fichero, con su localizador
│   ├── protocols/           disciplinas: escalera de autonomía, release gate, threat model, memoria…
│   └── patterns/            formas que se implementan en código: contratos de contexto, capacidades…
├── skills/                  ocho skills para Claude Code; citan knowledge/ por ruta, nunca lo copian
├── agents/isa/              cinco lentes de revisión, independientes, pensadas para correr en paralelo
├── schemas/                 once esquemas y plantillas: exactamente lo que el validador exige
└── tools/
    ├── isa_validate/        el validador stdlib: la negativa es un exit code y un campo señalado
    │   └── casos-negativos/ los dos artefactos que DEBEN fallar; el CI lo comprueba
    ├── generar_env/         escribe banco/.env.example desde el bloque `.env` del 0.4
    └── extraer_banco/   reconstruye banco/ desde libro.md (el libro no está en el repo)
```

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

## Lo que el CI comprueba

El workflow (`.github/workflows/promesas.yml`) no decora: cada paso es una promesa de este README convertida en verdicto. Que todo `.py` compila --- fragmentos incluidos, porque incompleto no es inválido ---; que todo YAML y JSON parsea; que `isa_validate` valida en verde los cuatro artefactos del libro **y sale con código 1, señalando el campo, sobre los dos negativos de `tools/isa_validate/casos-negativos/`**; que `banco/.env.example` cuadra con el sha256 que `generar_env.py` committea al generarlo; que los imports internos del árbol resuelven, que los nombres que el árbol usa están definidos y que toda tabla `banco.*` que el SQL usa tiene su `CREATE TABLE` (`tools/extraer_banco/tablas.py`).

Y la letra pequeña del badge, dicha de frente: **el verde del CI no acredita las cuatro comprobaciones que necesitan `libro.md`** --- las anclas del extractor (`--verificar`), la cobertura, la integridad y `generar_env.py --verificar` ---, porque la prosa del libro no se publica aquí. Ese paso salta en CI diciéndolo a gritos y las cuatro se ejecutan en local, donde vive `libro.md`; el sha256 committeado es lo que deja al CI vigilar `.env.example` aun sin el libro.

## Cómo se cita `knowledge/`

Tres reglas, y son las que evitan un paquete incoherente:

1. Cada `SKILL.md` abre con una sección `## Canon` que lista, **por ruta relativa entre backticks**, los ficheros que debe leer antes de actuar. Nunca por nombre de regla suelto, nunca por copia.
2. Esa sección cierra siempre con la misma frase: «Cita, nunca reproduzcas: si una regla no está en estos ficheros, no la apliques de memoria.»
3. Bidireccionalidad: si una skill está en los `owners` de un fichero de `knowledge/`, esa skill lo lee de verdad; y si lo lee, está en sus `owners`.

El libro se cita **por localizador** (`M21.4`, `15.6`, `A·H`), nunca textualmente. La única prosa citada literalmente en todo el paquete son las doce reglas del Anexo D en `INDEX.md` y una frase del 26.2. Todo lo demás está destilado --- que es a la vez higiene de ingeniería y la frontera que protege la prosa del libro.

## Añadir una regla

Una regla, un fichero, una fila en `INDEX.md`. `¿Cómo funciona la disciplina?` → `protocols/`. `¿Es una forma que se implementa en código?` → `patterns/`. `¿Es un dato que consume una herramienta?` → `schemas/`, no `knowledge/`. Por debajo de unas treinta líneas sustantivas, dentro de su fichero padre. El detalle está en `knowledge/INDEX.md`, y las reglas de contribución, en `CONTRIBUTING.md`.

## Nombrado

Todo artefacto lleva el prefijo `isa-`. Una excepción, la única del paquete: las lentes viven en `agents/isa/` con stem `isa-<rol>.md`, no `isa-isa-<rol>.md` --- en un plugin de una sola familia el prefijo *es* el segmento de familia.

## Estado

La versión completa que especifica `PLANO.md` --- las frases gatillo de cada skill y la escalera L0–L4 en línea --- está pendiente, igual que `CHANGELOG.md` y `plugin.json`. `tools/isa_validate/` ya existe: es el mecanismo real --- y no el criterio del modelo --- de las negativas que citan cuatro skills y cuatro ficheros de `knowledge/`. `PLANO.md` es el contrato de construcción, no documentación de usuario.

Las **erratas y actualizaciones** del libro se publican aquí.

## Licencia

MIT --- `Copyright (c) 2026 Antonio Carbonell`. Cubre el paquete entero, `banco/` incluido.

La licencia cubre el **código**. La **prosa** del libro sigue siendo del autor y con todos sus derechos: por eso aquí solo hay código, esquemas y criterio destilado, y ni una página citada.
