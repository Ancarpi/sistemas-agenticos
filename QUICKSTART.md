# QUICKSTART --- de `git clone` a algo corriendo

Tres escalones, de menos a más montaje. Cada comando de esta página se ha ejecutado antes de escribirlo; donde algo no se ha podido ejecutar sin tu clave, se dice.

## Escalón 0 --- sin montar nada (solo `python3`, sin dependencias)

El validador y el smoke test son stdlib puro. Recién clonado el repo:

```bash
# El validador, en verde sobre los cuatro artefactos del libro:
python3 tools/isa_validate/isa_validate.py context-contract banco/contratos/triage_sepa.contract.yaml
python3 tools/isa_validate/isa_validate.py capability       banco/tools/bloquear_tarjeta.capability.yaml
python3 tools/isa_validate/isa_validate.py eval-card        banco/evals/capstone_gate.eval.yaml
python3 tools/isa_validate/isa_validate.py agent-package    banco/catalogo/cards-disputes/agent.yaml
```

Y en rojo, que es la mitad que demuestra que valida de verdad:

```bash
python3 tools/isa_validate/isa_validate.py eval-card tools/isa_validate/casos-negativos/eval-card-sin-n-cases.yaml
# INVALIDO ...  metrics/0: falta n_cases        (sale con código 1)
```

El smoke test también corre sin nada montado, y ese es su trabajo: decirte exactamente qué falta.

```bash
cd banco && python3 smoke_test.py
#   alias agente-rapido       FALLA  falta en el .env: OPENAI_API_BASE, OPENAI_API_KEY
#   alias agente-equilibrado  FALLA  falta en el .env: OPENAI_API_BASE, OPENAI_API_KEY
#   postgres                  FALLA  falta DATABASE_URL en el .env
#   traza                     FALLA  falta en el .env: LANGSMITH_TRACING, LANGSMITH_API_KEY, LANGSMITH_PROJECT
#   0/4 pasan
```

Y sin ejecutar nada: `knowledge/INDEX.md` (las doce reglas), `schemas/` (lo que el validador exige) y `banco/MAPEO.md` (de qué página salió cada fichero) se leen tal cual.

## Escalón 1 --- Postgres con pgvector (Docker, ~2 minutos)

```bash
cd banco
docker compose up -d
docker compose exec -T db psql -U banco -d banco -v ON_ERROR_STOP=1 < db/schema.sql
```

Comprobado sobre este repo: la imagen es `pgvector/pgvector:pg17`, y el `schema.sql` aplica limpio **dos veces seguidas** con `ON_ERROR_STOP=1` --- exit 0 en ambas pasadas, `vector 0.8.6` instalado y los roles `agente_lectura` y `banco_app` creados con el rodeo `DO $do$` que `CREATE ROLE` obliga a usar. Es reaplicable de verdad, que es lo que promete su primera línea.

## Escalón 2 --- el gateway y una clave de proveedor (lo que el libro monta en el 0.5)

Esto ya pide algo que este repo no puede darte: una clave de un proveedor de modelos. Con ella:

```bash
cd banco
uv sync                      # las versiones fijadas del 0.4 resuelven (166 paquetes)
cp .env.example .env         # y rellenar: gateway, DATABASE_URL, LangSmith
# el gateway LiteLLM se levanta aparte: su config.yaml está en gateway/,
# y el `docker run` que lo arranca, en el 0.5 del libro
uv run python smoke_test.py  # el objetivo: 4/4 pasan
```

Que `uv sync` resuelve está comprobado (`uv lock` sobre este `pyproject.toml`: 166 paquetes, sin conflicto). El `4/4` final no se puede comprobar por ti: exige tu clave y tu gateway en pie. Si algo falla ahí, el propio smoke test te dice qué fila y por qué, en una línea y no en un traceback.

A partir de aquí, `banco/README.md` es el mapa: qué fichero corre con qué comando, cuáles necesitan a sus hermanos en el `PYTHONPATH` y cuáles son fragmentos a propósito.

## Lo que NO corre, dicho de frente

- **Los fragmentos didácticos** (`grafo_conciliacion.py`, `medidas.py`, `memoria.py`...) no se completan montando infraestructura: les falta el código que el libro te deja como ejercicio. La lista exacta, con qué le falta a cada uno, está en `banco/README.md`.
- **`uv run pytest tests/` falla hoy.** El test del 16.7 lee `compliance/clasificacion-ia.yaml`, y ese YAML cita sus evidencias con las rutas planas del libro (`cumplimiento.py`) mientras que el árbol del Ejercicio 0.1 las coloca en `src/core/`. Es una costura de la misma familia que las de `COSTURAS.md`; como todo `banco/`, se corrige en el libro y se re-extrae, no editando aquí.
- **`tools/extraer_banco/`** necesita `libro.md`, que no se publica en este repo. Sin el libro fuente, el extractor no tiene nada que extraer; el árbol ya extraído es `banco/`.
