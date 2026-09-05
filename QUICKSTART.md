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
# El rol banco_app del 16.6 nace sin contraseña, y es el rol con el que se
# conecta tests/test_registro.py: la RLS no se mide con un superusuario.
docker compose exec -T db psql -U banco -d banco \
    -c "ALTER ROLE banco_app PASSWORD 'local-desechable'"
cp .env.example .env         # para los tests bastan las dos DATABASE_URL
uv run pytest tests/         # 3 passed
```

Comprobado sobre este repo: la imagen es `pgvector/pgvector:pg17`, y el `schema.sql` aplica limpio **dos veces seguidas** con `ON_ERROR_STOP=1` --- exit 0 en ambas pasadas, `vector 0.8.6` instalado y los roles `agente_lectura` y `banco_app` creados con el rodeo `DO $do$` que `CREATE ROLE` obliga a usar. Es reaplicable de verdad, que es lo que promete su primera línea. Y con eso los tres tests del 16.7 pasan, que es la única fila de la tabla de `banco/README.md` que se comprueba sin gateway.

## Escalón 2 --- el gateway y una clave de proveedor (lo que el libro monta en el 0.5)

Esto ya pide algo que este repo no puede darte: una clave de un proveedor de modelos. Con ella:

```bash
cd banco
uv sync                      # las versiones fijadas del 0.4 resuelven (166 paquetes)
cp .env.example .env         # y rellenar el resto: gateway y LangSmith
# el gateway LiteLLM se levanta aparte: su config.yaml está en gateway/,
# y el `docker run` que lo arranca, en el 0.5 del libro
uv run python smoke_test.py  # el objetivo: 4/4 pasan
```

Que `uv sync` resuelve está comprobado (`uv lock` sobre este `pyproject.toml`: 166 paquetes, sin conflicto). El `4/4` final no se puede comprobar por ti: exige tu clave y tu gateway en pie. Si algo falla ahí, el propio smoke test te dice qué fila y por qué, en una línea y no en un traceback.

A partir de aquí, `banco/README.md` es el mapa: qué fichero corre con qué comando, cuáles necesitan a sus hermanos en el `PYTHONPATH` y cuáles son fragmentos a propósito.

## Lo que NO corre, dicho de frente

- **Los fragmentos didácticos** (`grafo_conciliacion.py`, `medidas.py`, `indexar.py`...) no se completan montando infraestructura: les falta el código que el libro te deja como ejercicio. La lista exacta, con qué le falta a cada uno, está en `banco/README.md`.
- **`uv run pytest tests/` sin `.env` no ejecuta ni un test, y lo dice en la cabecera.** `src/core/cumplimiento.py` abre su pool a nivel de módulo, así que sin `DATABASE_URL` el import de `tests/test_art50.py` muere y pytest aborta la tanda entera. Con el `.env` puesto y sin Postgres son `2 passed, 1 failed`: el que falla es el test de RLS del 16.6, contra una base de datos que no está. Falla en vez de saltarse, y eso es el resultado correcto.
- **`tools/extraer_banco/`** necesita `libro.md`, que no se publica en este repo. Sin el libro fuente, el extractor no tiene nada que extraer; el árbol ya extraído es `banco/`.
