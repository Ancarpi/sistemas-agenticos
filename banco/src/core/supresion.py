# src/core/supresion.py --- la operación distribuida del 34.6:
# los siete almacenes en el orden en que aquel apartado los
# cuenta, y un `MemoryDeletionReceipt` que dice cuál se borró,
# cuál se redactó y cuál sigue pendiente. Los tipos, la conexión
# y el `ANOTAR` salen del memoria.py; aquí solo se borra.
import json

from src.core import hitl, trabajos   # la firma del 35.6, la cola del 21.5
from src.core.memoria import (ANOTAR, SIETE, TENANT,
                              AlmacenBorrado,
                              MemoryDeletionReceipt, conectar,
                              existe, parte, sin_personal)
from trazas import PERSONAL               # el regex del 36.6

# Los estados vivos de la cola del 21.5: el caso a medias no se
# borra, se bloquea.
VIVOS = ("pending", "leased", "running", "waiting_human",
         "retry_scheduled")


def _literal(s: str) -> str:
    """Escapa `%`, `_` y la barra invertida antes de meter `s`
    en un patrón LIKE. El sujeto viene de FUERA, y en un id
    legítimo como C_1 el guion bajo es parte del id, no un
    comodín: sin esto, suprimir C_1 barre el store y los
    checkpoints de CX1 --- las filas de OTRO cliente."""
    for comodin in ("\\", "%", "_"):
        s = s.replace(comodin, "\\" + comodin)
    return s


def _a1_store(cur, c) -> AlmacenBorrado:
    # Dos tablas y no una: la gobernada del memoria.sql y la que
    # crea el setup() del PostgresStore (6.2), donde escribe todo
    # agente que no pase por la API tipada del 34.5.
    cur.execute("DELETE FROM banco.memoria WHERE sujeto = %s"
                " RETURNING source_run_id", (c["sujeto"],))
    filas = cur.fetchall()
    c["runs"] = sorted({f["source_run_id"] for f in filas})
    # El namespace del store es (tenant, propósito, sujeto) y el
    # propósito se barre con comodín: lo que un agente escribió a
    # pelo bajo banco.soporte.C-99 también es del sujeto, y
    # barrer solo `preferencias` lo dejaría vivo sin receipt.
    n = len(filas)
    suj = _literal(c["sujeto"])
    like = (f"{TENANT}.%.{suj}", f"{TENANT}.%.{suj}.%")
    for t in ("store_vectors", "store"):
        if existe(cur, t):
            cur.execute(f"DELETE FROM {t} WHERE prefix LIKE %s"
                        " OR prefix LIKE %s", like)
            n += cur.rowcount
    tablas = ["banco.memoria", "store", "store_vectors"]
    return parte(0, tablas, "borrado", n, "DPO")


def _a2_checkpoints(cur, c) -> AlmacenBorrado:
    # Se encuentran porque el `hilo()` del 18.3 pone el sujeto
    # DENTRO del thread_id. Con un uuid ahí, este almacén queda
    # inalcanzable, y eso es un defecto de diseño, no de aquí.
    n = 0
    for t in ("checkpoint_writes", "checkpoints"):
        if existe(cur, t):
            cur.execute(f"DELETE FROM {t} WHERE thread_id LIKE"
                        " %s", ("%:" + _literal(c["sujeto"]),))
            n += cur.rowcount
    tablas = ["checkpoints", "checkpoint_writes"]
    return parte(1, tablas, "borrado", n, "Plataforma")


def _a3_resumenes(cur, c) -> AlmacenBorrado:
    # El resumen no tiene columna: es un valor de canal dentro
    # del blob, y por eso se borra el HILO y no el campo.
    n = 0
    if existe(cur, "checkpoint_blobs"):
        cur.execute("DELETE FROM checkpoint_blobs WHERE thread_id"
                    " LIKE %s", ("%:" + _literal(c["sujeto"]),))
        n = cur.rowcount
    cur.execute("SELECT detalle::text AS t FROM banco.registro_ia"
                " WHERE sujeto = %s", (c["sujeto"],))
    sucias = sum(1 for f in cur.fetchall()
                 if PERSONAL.search(f["t"]))
    if sucias:
        return parte(
            2, ["checkpoint_blobs", "banco.registro_ia"],
            "bloqueado", n, "Plataforma", None,
            f"{sucias} filas de prosa en una tabla de solo"
            " añadir: no hay DELETE que las alcance")
    return parte(2, ["checkpoint_blobs"], "borrado", n,
                 "Plataforma")


def _a4_trazas(cur, c) -> AlmacenBorrado:
    return parte(
        3, ["langsmith", "siem", "audit_lake"], "delegado",
        len(c["runs"]), "Observabilidad", 30,
        "fuera de esta base: se pide al dueño con la lista de"
        " run_id que este receipt deja escrita")


def _a5_auditoria(cur, c) -> AlmacenBorrado:
    # PRIMERO se cierra, LUEGO se redacta: la pendiente del
    # sujeto que solo se vaciara quedaría en `pendientes` como
    # `{}`, firmable a ciegas. El rechazo lo firma el 35.6
    # (`sistema:supresion`), no este fichero, y en su propia
    # conexión: cerrado queda aunque esto se caiga después.
    hitl.cerrar_por_supresion(c["sujeto"])
    cur.execute(
        "UPDATE banco.aprobaciones SET propuesta = '{}'::jsonb,"
        " diff = NULL, purgado_en = now(), purgado_por = %s"
        " WHERE sujeto = %s AND purgado_en IS NULL",
        (c["quien"], c["sujeto"]))
    red = cur.rowcount
    cur.execute("SELECT count(*) AS n FROM banco.registro_ia"
                " WHERE sujeto = %s", (c["sujeto"],))
    return parte(
        4, ["banco.aprobaciones", "banco.registro_ia"],
        "redactado", red, "Cumplimiento", None,
        f"se conservan {cur.fetchone()['n']} filas del registro"
        " del 16.6 (Art. 19 y 26(6)) sin el dato dentro")


def _a6_corpus(cur, c) -> AlmacenBorrado:
    # Un embedding no se edita: se reindexa. Borrar los trozos
    # deja el documento incompleto y un trabajo en la cola del
    # 21.5 para su dueño, que es quien lo republica sin el dato.
    cur.execute("DELETE FROM banco.manuales WHERE sujeto = %s"
                " RETURNING fuente", (c["sujeto"],))
    trozos = cur.fetchall()
    c["fuentes"] = sorted({f["fuente"] for f in trozos})
    for f in c["fuentes"]:
        trabajos.encolar(cur, "reindexar", f,
                         {"fuente": f, "motivo": "supresion"},
                         prioridad=5)
    # `filas` cuenta filas, como promete el DDL: los TROZOS que
    # cayeron, no las fuentes. Dos trozos de un documento son dos
    # filas borradas y un solo trabajo de reindexado.
    return parte(5, ["banco.manuales"], "borrado", len(trozos),
                 "Productos")


def _a7_trabajos(cur, c) -> AlmacenBorrado:
    clave = json.dumps({"cliente": c["sujeto"]})
    cur.execute("SELECT count(*) AS n FROM banco.trabajos WHERE"
                " carga @> %s::jsonb AND estado = ANY(%s)",
                (clave, list(VIVOS)))
    vivos = cur.fetchone()["n"]
    cerrados = ("SELECT id FROM banco.trabajos WHERE carga @>"
                " %s::jsonb AND estado IN ('completed',"
                " 'dead_letter')")
    cur.execute("DELETE FROM banco.efectos WHERE trabajo_id IN"
                f" ({cerrados})", (clave,))
    n = cur.rowcount
    cur.execute(f"DELETE FROM banco.trabajos WHERE id IN"
                f" ({cerrados})", (clave,))
    n += cur.rowcount
    tablas = ["banco.trabajos", "banco.efectos"]
    if vivos:
        # Borrar el trabajo de una devolución en vuelo pierde
        # dinero, así que el caso abierto se bloquea y el
        # receipt lo dice con su número.
        return parte(6, tablas, "bloqueado", n, "Operaciones",
                     None, f"sin cerrar: {vivos}; caen con su"
                           " trabajo")
    return parte(6, tablas, "borrado", n, "Operaciones")


ALMACENES = (_a1_store, _a2_checkpoints, _a3_resumenes,
             _a4_trazas, _a5_auditoria, _a6_corpus, _a7_trabajos)


def suprimir_sujeto(sujeto: str, solicitud: str, quien: str,
                    motivo: str = "user_request",
                    ) -> MemoryDeletionReceipt:
    """La supresión distribuida del 34.6, en UNA transacción. No
    es un @tool y no debe serlo: ningún modelo abre un
    expediente de supresión."""
    c = {"sujeto": sujeto, "quien": quien, "runs": [],
         "fuentes": []}
    with conectar(autocommit=False) as cx, cx.cursor() as cur:
        partes = [fn(cur, c) for fn in ALMACENES]
        for p in partes:
            cur.execute(ANOTAR, (solicitud, sujeto, p.almacen,
                                 p.tablas, p.accion, p.filas,
                                 p.dueno, p.plazo_dias, p.base,
                                 quien))
        pendientes = [p.almacen for p in partes
                      if p.accion in ("delegado", "bloqueado")]
        hecho = {"solicitud": solicitud, "motivo": motivo,
                 "pendientes": pendientes,
                 "almacenes": {p.almacen: [p.accion, p.filas]
                               for p in partes}}
        # El hecho sin el dato dentro, comprobado antes de
        # escribirlo en una tabla que solo admite INSERT.
        sin_personal({"hecho": json.dumps(hecho)})
        cur.execute(
            "INSERT INTO banco.registro_ia (tipo, canal, sujeto,"
            " detalle) VALUES ('rgpd_supresion', 'backend', %s,"
            " %s) RETURNING ts", (sujeto, json.dumps(hecho)))
        ts = cur.fetchone()["ts"]
    return MemoryDeletionReceipt(
        solicitud=solicitud, sujeto=sujeto, motivo=motivo,
        ejecutado_por=quien, ts=ts, almacenes=partes,
        completo=not pendientes, pendientes=pendientes)


if __name__ == "__main__":
    import sys
    import textwrap

    from src.core.memoria import purgar_caducadas

    sujeto, solicitud, quien = sys.argv[1:4]
    r = suprimir_sujeto(sujeto, solicitud, quien)
    print(f"\nSUPRESIÓN {r.solicitud} · {r.sujeto} · por"
          f" {r.ejecutado_por} · {r.ts:%Y-%m-%d %H:%M}")
    for a in r.almacenes:
        print(f"  {a.accion:<10} {a.filas:>3} filas  {a.almacen}"
              f"  [{a.dueno}]")
        for t in textwrap.wrap(a.base or "", 56):
            print(f"             · {t}")
    print(f"  completo={r.completo}  pendientes={r.pendientes}")
    print(f"\nTTL vencido: {purgar_caducadas()}")
