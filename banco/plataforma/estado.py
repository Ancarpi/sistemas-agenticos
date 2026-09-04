# estado.py --- un pool, un checkpointer y un store para todo el
# proceso, y no uno por agente. El 37.2 los declara en su
# `runtime.py`; en cuanto hay un segundo proceso, salen aquí.
import os

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from src.core.models import get_embeddings      # el 0.4

ENTORNO = os.environ["ENTORNO"]   # se fija al importar, y nadie
SAVER = STORE = None              # lo reescribe; estos dos, si


async def arrancar():
    """En el `lifespan` del 17.2 antes del `yield`, y en el 11.5
    antes de la primera tanda; el `if` evita el segundo pool."""
    global SAVER, STORE
    if SAVER is not None:
        return
    kw = {"autocommit": True, "row_factory": dict_row}
    pool = AsyncConnectionPool(os.environ["DATABASE_URL"],
                               open=False, kwargs=kw)
    await pool.open()
    SAVER, STORE = AsyncPostgresSaver(pool), AsyncPostgresStore(
        pool, index={"embed": get_embeddings(), "dims": 1024})
    await SAVER.setup()
    await STORE.setup()


# 37.2 runtime.py: fuera sus globales y `arrancar()`; y a `estado.`
# los dos `SAVER`/`STORE` de `compilar` y el `ENTORNO` de `ejecutar`.
