# banco

El repositorio de referencia de **«Ingeniería de Sistemas Agénticos --- Manual completo de LangChain y LangGraph»**, de Antonio Carbonell.

El caso único del libro: un banco ficticio con un back-office de incidencias SEPA, cinco superficies sobre un solo cerebro y un Postgres detrás. Aquí está el código de ese caso, en el árbol que el Ejercicio 0.1 impone, para que puedas leerlo, ejecutar lo que se ejecuta y comparar tu versión con la del libro.

**Esto no sustituye al libro.** El código es la mitad barata; el criterio que decide *cuándo* un agente puede actuar solo, *qué* mide una puerta de release y *qué* no entra en una traza está en las páginas, no en los ficheros. Si has llegado aquí sin el libro, te falta la parte que importa.

---

## Ninguna línea de este repo se escribió a mano

El libro es la fuente y este árbol es la salida. Lo produce un script a partir de `libro.md`:

```
python3 ../tools/extraer_banco/extraer_banco.py            # extrae
python3 ../tools/extraer_banco/extraer_banco.py --verificar # solo comprueba
```

El mapeo vive una sola vez y como datos, en `../tools/extraer_banco/mapeo.yaml`. Cada bloque declara sus dos anclas --- su primera y su última línea ---, así que **si el libro se edita y las líneas se mueven, la extracción falla en voz alta** en vez de escribir basura; `--resincronizar` reubica los rangos por ancla y te deja el diff para revisar. El día que cambie una página, se vuelve a ejecutar el script y el repo está al día.

Consecuencia práctica: **no edites estos ficheros.** Se edita `mapeo.yaml`, o se edita el libro. Los cambios locales los pisa la siguiente extracción.

- **`MAPEO.md`** --- generado. Qué módulo del libro entrega cada fichero, con las líneas exactas. Es la tabla que buscas si te preguntas de dónde salió algo.
- **`COSTURAS.md`** --- generado. Los fragmentos que el libro deja para pegar a mano, y dónde van.

Siete ficheros de este directorio no los escribe el extractor. Cuatro son el empaquetado y se editan a mano: `README.md`, `pyproject.toml`, `docker-compose.yml` y `conftest.py`. Dos son artefactos del libro traducidos a datos, también a mano: `contratos/triage_sepa.contract.yaml` (el `TRIAGE_CONTRACT` del 19.1, de dataclass a YAML) y `evals/capstone_gate.eval.yaml` (la tabla del 18.4, con el 246 que el 15.7 justifica en vez del 120 impreso). El séptimo, `.env.example`, también sale del libro, solo que por otro script: lo genera `../tools/generar_env/generar_env.py` desde el bloque `.env` del 0.4, y ese script sale con código 1 y nombra la variable cuando algo de este árbol lee con `os.environ` una que el libro no declara.

## Qué corre y qué no

El libro es didáctico: algunos bloques son ficheros completos y otros son fragmentos que ilustran una idea. Se han extraído tal cual, comentarios incluidos, porque tienen que coincidir con la página impresa. Eso significa que **este repo no arranca entero de un `uv run`, y decirlo es más útil que fingir lo contrario.** Tres niveles:

**1. Corre.** Con `.env` puesto, Postgres arriba y el gateway del 0.5 en pie:

| Fichero | Cómo | Módulo |
|---|---|---|
| `smoke_test.py` | `uv run python smoke_test.py` | Ej. 0.1 |
| `src/agents/nano_agent.py` | `PYTHONPATH=. uv run python src/agents/nano_agent.py` | 3.3 |
| `src/agents/supervisor/supervisor.py` | `PYTHONPATH=. uv run python src/agents/supervisor/supervisor.py` | 9.2 |
| `src/rag/hibrida.py` | `uv run python -m src.rag.hibrida "comisión por devolver la REF-4471"` | 8.1 |
| `db/schema.sql`, `src/rag/08_hibrida.sql` | `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/schema.sql` | 7.6, 16.6, 8.1 |
| `tests/` (los cuatro) | `uv run pytest tests/` | 16.7, 34.6 |

Esa última fila es la que más letra pequeña tiene, así que va entera. `pytest` se ejecuta desde `banco/`, y necesita dos cosas que el árbol del Ejercicio 0.1 no da solo. Las dos están puestas: el `pythonpath` de `[tool.pytest.ini_options]` en `pyproject.toml`, porque `tests/test_art50.py` importa `cumplimiento` plano, igual que el libro, y aquí ese fichero vive en `src/core/` --- y `plataforma/` va en la misma lista, porque `tests/test_supresion.py` importa la supresión del 34.6 y esta llega a `trazas` igual de plano vía `memoria.py`; y `conftest.py`, que carga el `.env`, porque `src/core/cumplimiento.py` abre su pool a nivel de módulo y sin `DATABASE_URL` el import muere antes de la primera aserción, pytest aborta la tanda entera y ejecuta cero tests. Si falta el `.env`, la cabecera de pytest lo dice en una línea.

Comprobado sobre este árbol: con `.env` puesto y Postgres arriba, `5 passed`. Con `.env` puesto y sin Postgres, `2 passed, 1 failed, 2 skipped`, y ese reparto es el resultado correcto: `tests/test_registro.py` mide la RLS del 16.6 contra la base de datos, y un test de RLS sin base de datos no mide nada. Falla, y no se salta. Lo que sale es `psycopg.OperationalError: connection failed`. Ese test se conecta con `DATABASE_URL_APP`, que es el rol `banco_app` del 16.6 y no el superusuario, por lo que dice la arruga de abajo. Los dos `skipped` son `tests/test_supresion.py` --- los dos casos negativos que el red team dejó sobre la supresión del 34.6: que un guion bajo en el sujeto no actúe de comodín del `LIKE` y borre filas de OTRO cliente, y que una propuesta pendiente del sujeto se cierre firmada antes de purgarse, en vez de quedar vaciada y aprobable a ciegas ---, y saltar es su resultado correcto: miden código de aplicación, no una promesa del schema, y sin base de datos no mienten ni en rojo ni en verde.

**2. Corre con sus hermanos en el `PYTHONPATH`.** El libro pone estos ficheros unos al lado de otros y los importa planos --- `from herramientas import ...`, `from canal_chat import canal_chat` ---, mientras que el Ejercicio 0.1 los reparte por `src/`. Los dos son correctos y son incompatibles, y no se ha tocado ni un `import` para disimularlo. Se resuelve al ejecutar:

```
PYTHONPATH=.:src/agents:src/agents/backoffice:src/agents/conciliacion:src/channels/chat \
  uv run python src/channels/chat/servidor.py
```

Afecta a `herramientas.py` y `agente_backoffice.py` (4.1, 4.3), `canal_chat.py`, `servidor.py` y `webhook_slack.py` (6.3, 12.5, 12.6), `batch_nocturno.py` (11.5), `agente_voz.py` (13.4) y `cara.py` (14.2). La alternativa honesta es la del libro: copia los cuatro ficheros de un canal a un directorio y ejecútalos ahí.

La pareja de la memoria del M34 está en el mismo caso, con `plataforma/` como hermano: `memoria.py` (34.5) importa `trazas` plano y `supresion.py` (34.6) se apoya en él, así que `python -m src.core.supresion` muere en `ModuleNotFoundError: No module named 'trazas'` hasta que ese directorio entra en el path. Con él puesto, y con Postgres arriba, la supresión corre entera e imprime su receipt de siete almacenes:

```
PYTHONPATH=.:plataforma \
  uv run python -m src.core.supresion C-99 EXP-2026-0001 dpo:ana
```

`memoria.py` no tiene `__main__`: se importa --- sus tres `@tool` del 34.5 --- o lo ejercita `tests/test_supresion.py`.

**3. Son fragmentos y no importan.** A propósito, y el libro lo dice en cada caso. No están rotos: están incompletos.

| Fichero | Qué le falta |
|---|---|
| `src/agents/conciliacion/grafo_conciliacion.py` | Andamio del Ejercicio 5.1. El libro nunca lo publica entero y aun así lo importa en el 6.3 y en el 12.5. Falta teclear los nodos. |
| `src/evals/medidas.py` | Andamio del Ejercicio 31.1. Las seis medidas se escriben contra *tus* entrypoints; el libro no las da. Cada una lanza `NotImplementedError` con su encargo. |
| `src/agents/cards_disputes/herramientas.py` | El 20.2 enseña la barrera dry-run/commit: `policy_engine`, `transaction` y `cards_core` son tu infraestructura. |
| `src/rag/indexar.py` | El 7.4 es un fragmento de seis líneas: le falta el `import os` y de dónde salen los `chunks`. |
| `plataforma/runtime.py` | El 37.2 es la costura de una plataforma: `plataforma.catalogo`, `hitl`, `registro` y `trazas` son el ejercicio del módulo. |
| `src/agents/allowlist_mcp.json` | Los sha256 son marcadores. La primera versión real la escribes pegando la salida del bucle de `cliente_core.py` y revisándola (Ej. 10.1). |
| `.github/workflows/agent-evals.yml` | Extracto conceptual, igual que en el libro. |
| `src/agents/cliente_core.py` | Corre, pero lee la allow-list en `docs/mcp-aprobadas.json`: ver `COSTURAS.md`. |

## Arrancar

```bash
cp .env.example .env          # generado del 0.4; sin OPENAI_API_BASE no hay nada que hacer
uv sync                       # núcleo. --extra chat para M12/M17, --extra voz para M13/M14
docker compose up -d          # Postgres con pgvector
docker compose exec -T db psql -U banco -d banco \
    -v ON_ERROR_STOP=1 < db/schema.sql
uv run python smoke_test.py   # cuatro comprobaciones y un resumen tabulado
```

El gateway LiteLLM va aparte: su `config.yaml` está en `gateway/`, y el `docker run` que lo levanta, en el 0.5. **Sin gateway no hay alias**, y todo este repo habla alias --- `agente-rapido`, `agente-equilibrado`, `agente-listo`, `emb-multilingue`, `rerank-multilingue` ---, nunca el identificador de un proveedor. Si no quieres gateway, `src/core/models_local.py` es la salida de emergencia del 0.5 y resuelve los alias en la propia fábrica.

Se anuncia reaplicable y lo es: comprobado sobre este árbol, el fichero entero aplica con `ON_ERROR_STOP=1` dos veces seguidas y sale con 0 en las dos pasadas, porque el `CREATE ROLE banco_app` del 16.6 lleva el rodeo con `DO $do$` del 7.6. Queda una arruga, y es del libro y no del empaquetado:

- Ese rol nace sin contraseña. Dale una antes de ponerlo en tu `DATABASE_URL_APP`, que es la variable que el 0.4 reserva para él, y **usa ese rol y no el superusuario**: la RLS del 7.6 y del 16.6 no vale nada contra un `BYPASSRLS`, y el superusuario es el `DATABASE_URL` por defecto de casi cualquier portátil.

## Secretos

No hay ninguno. Todo son `os.environ/`, y los dos `.env` son `.example` con los valores vacíos. Si algún día aparece un valor real en un fichero de este árbol, es un fallo de la extracción: el libro no los tiene.

## Licencia

MIT --- `Copyright (c) 2026 Antonio Carbonell`. El texto está en el `LICENSE` de la raíz del paquete, y cubre también este directorio.

La licencia cubre el **código**. La **prosa** del libro sigue siendo del autor y con todos sus derechos: por eso aquí solo hay código y comentarios de código, y por eso el resto del paquete destila el criterio en vez de citarlo.

El libro, en Amazon --- *Ingeniería de Sistemas Agénticos*, Antonio Carbonell, primera edición, septiembre de 2026. (El enlace se añadirá cuando el ASIN exista: un `amazon.es/dp/` sin ASIN es un 404, y `tools/extraer_banco/imports.py` falla si reaparece.)
