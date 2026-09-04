# src/ops/migrar_checkpoints.py --- lleva el estado persistido de
# una versión del grafo a la siguiente. Se corre a mano, dos veces:
#   uv run python -m src.ops.migrar_checkpoints            # cuenta
#   uv run python -m src.ops.migrar_checkpoints --aplicar  # escribe
import argparse
import asyncio
import os
from collections import Counter

import psycopg
from psycopg.rows import dict_row

from grafo_conciliacion import obtener_app    # la fábrica del 5.3

VERSION_ESTADO = 3     # la que espera el código de HOY, y una
# clave más de `EstadoBackoffice` (5.3). El checkpoint que no la
# trae es anterior a que la clave existiera: por definición, v1.


class NoMigra(Exception):
    """El hilo no sube sin inventarse un dato. Se cuenta, se
    aparta y se deja INTACTO donde está."""


def v1_a_v2(s: dict) -> dict:
    """`movimientos` sale del estado: era el historial del core
    reescrito en cada superpaso, justo lo que el 5.2 prohíbe, y el
    nodo `investigar` lo rehidrata. Y entra `tenant`, que el `ns`
    de memoria del 37.2 exige y no puede salir de la nada."""
    if not s.get("referencia"):
        raise NoMigra("sin referencia")
    return {"movimientos": [], "tenant": "banco.sepa"}


def v2_a_v3(s: dict) -> dict:
    """`resuelto: bool` pasa a `estado_caso`, porque un booleano no
    distingue las tres salidas que el 11.5 ya cuenta por separado
    (resuelta, escalada, dlq). Migración CON PÉRDIDA, y declarada:
    lo escalado antes de v3 no es distinguible y sale `abierto`."""
    return {"estado_caso": "resuelta" if s.get("resuelto")
            else "abierto"}


# Por SALTO, no de v1 a v3: el hilo que lleva seis meses parado en
# una aprobación sube los dos peldaños, y el de v2 solo el suyo.
SALTOS = {1: v1_a_v2, 2: v2_a_v3}


def exigir_version(estado: dict) -> None:
    """La otra mitad, y no vive aquí: va en la primera línea del
    `triage` del 5.3, que ya tiene el estado delante y no paga un
    viaje más. Un hilo apartado no se reanuda a ciegas: para con
    su versión puesta, y quien lo abrió lee un número en vez de un
    KeyError tres nodos más allá."""
    v = estado.get("version_estado", 1)
    if v != VERSION_ESTADO:
        raise RuntimeError(
            f"estado v{v}; este código espera v{VERSION_ESTADO}")


async def hilos() -> list[str]:
    """No hay API para «dame los hilos»: `alist(None)` devuelve
    checkpoints, y contar hilos por ahí son millones de filas en
    un Postgres con seis meses de historia. Este es el único sitio
    del libro que lee las tablas del checkpointer a pelo."""
    async with await psycopg.AsyncConnection.connect(
            os.environ["DATABASE_URL"], row_factory=dict_row) as cx:
        cur = await cx.execute(
            "SELECT DISTINCT thread_id FROM checkpoints"
            " WHERE checkpoint_ns = '' ORDER BY thread_id")
        return [f["thread_id"] for f in await cur.fetchall()]


async def plan(app, hilo: str) -> tuple[str, dict | None]:
    """Decide y no escribe. Lo MISMO corre en seco y en la pasada
    real, y por eso el recuento de la primera es el resultado de
    la segunda: un dry-run que calcula por otro camino cuenta otra
    cosa distinta de la que luego va a pasar."""
    cfg = {"configurable": {"thread_id": hilo}}
    valores = dict((await app.aget_state(cfg)).values)
    v = valores.get("version_estado", 1)
    if v == VERSION_ESTADO:
        return "al día", None
    parche = {}
    while v < VERSION_ESTADO:
        if v not in SALTOS:
            return f"versión {v} sin salto", None
        try:
            trozo = SALTOS[v](valores)
        except NoMigra as e:
            return f"no migra ({e})", None
        valores.update(trozo)   # el salto siguiente lee lo que
        parche.update(trozo)    # dejó el anterior, no el original
        v += 1
    parche["version_estado"] = VERSION_ESTADO
    # `aupdate_state` escribe COMO UN NODO: cada clave pasa por su
    # reducer. `messages` lleva `add_messages` (5.3), así que un
    # parche con mensajes los AÑADE en vez de sustituirlos.
    assert "messages" not in parche, "para mensajes, RemoveMessage"
    return "migra", parche


async def main(aplicar: bool, apartados_en: str) -> None:
    app = await obtener_app()
    n, apartados = Counter(), []
    for hilo in await hilos():
        veredicto, parche = await plan(app, hilo)
        n[veredicto.split(" (")[0]] += 1
        if parche is None:
            if veredicto != "al día":
                apartados.append(f"{hilo}\t{veredicto}")
        elif aplicar:
            await app.aupdate_state(
                {"configurable": {"thread_id": hilo}}, parche)
    # El fichero se escribe TAMBIÉN en seco: la lista de los que
    # fallarían es el entregable de la pasada en seco, y quien
    # decide si la migración sale hoy la lee entera.
    with open(apartados_en, "w") as f:
        f.write("\n".join(apartados))
    for k, v in sorted(n.items()):
        print(f"{v:>7}  {k}")
    print(f"{len(apartados):>7}  APARTADOS -> {apartados_en}")
    print("aplicado" if aplicar else
          "en seco: no se ha escrito un solo checkpoint")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--aplicar", action="store_true")
    p.add_argument("--apartados", default="docs/apartados.tsv")
    a = p.parse_args()
    asyncio.run(main(a.aplicar, a.apartados))
