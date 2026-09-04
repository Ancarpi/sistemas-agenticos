from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class MemoryRecord(BaseModel):
    namespace: tuple[str, ...]        # ('retail', 'soporte', 'C-99')
    key: str                         # 'preferred_language'
    value: dict
    source_run_id: str
    sensitivity: Literal['public','internal','confidential','restricted']
    confidence: float
    ttl_days: int | None
    consent_basis: str | None
    owner: str
    created_at: datetime
    expires_at: datetime | None


# --- anadido del M34.7 (extraer_banco) ---
# Anadido del M34.7.
# src/core/memoria.py --- las tres APIs del 34.5 con cuerpo, sus
# tres receipts definidos, el TTL por tipo y el olvido de una
# clave. Los siete almacenes de la supresión distribuida del 34.6
# los cierra el supresion.py de al lado. La cola y la firma NO se
# escriben aquí: son el `hitl.py` del 35.6. Antes: el memoria.sql.
# Cursores con `row_factory=dict_row`, como el pool del 32.2.
import hashlib
import json
import os
from datetime import datetime
from typing import Literal

import psycopg
from psycopg.rows import dict_row
from pydantic import BaseModel

from src.core import hitl                # la cola del 35.6
from trazas import PERSONAL              # el regex del 36.6

DB = os.environ["DATABASE_URL"]
TENANT = os.environ.get("TENANT", "banco")
CLAVES = ("idioma", "canal_preferido", "formato_resumen")
TIPOS = ("faq", "eval_case", "playbook", "policy_candidate")
CONSENTIMIENTO = "consentimiento:declarado_en_conversacion"
# Los siete del 34.6 en el orden en que aquel apartado los cuenta.
# La lista es el hallazgo, así que aquí es una constante.
SIETE = ("1 store", "2 checkpoints", "3 resúmenes", "4 trazas",
         "5 auditoría", "6 corpus RAG", "7 cola y outbox")


class MemoriaRechazada(Exception):
    """Clave fuera de catálogo, procedencia inventada o un valor
    que parece un dato personal."""


def _sin_runtime() -> dict:
    raise MemoriaRechazada("memoria: sin contexto de run (37.2)")


# El run y el humano que delegó NO están en la firma del 34.5, y
# es deliberado: una procedencia que pone el modelo no es una
# procedencia. Los pone el runtime del 37.2 en una línea,
# `memoria.CTX = lambda: get_runtime().context`.
CTX = _sin_runtime


class MemoryWriteReceipt(BaseModel):
    """Qué entró, con qué permiso, de qué run y hasta cuándo."""
    namespace: tuple[str, ...]
    clave: str
    tipo: str
    owner: str
    sensibilidad: str
    consent_basis: str | None
    source_run_id: str
    evidencia: str
    aprobado_por: str | None
    creado_en: datetime
    expira_en: datetime | None
    revertir: str                  # la llamada que la deshace


class MemoryProposalReceipt(BaseModel):
    """Que NO se publicó nada: la fila pendiente de la cola del
    35.6 y el `count` del namespace, igual antes y después."""
    referencia: str
    dominio: str
    tipo: str
    propuesta_id: int
    hilo: str
    evidencias_run_ids: list[str]
    publicado: bool
    colectivas_antes: int
    colectivas_despues: int
    estado: str


class AlmacenBorrado(BaseModel):
    almacen: str
    tablas: list[str]
    accion: Literal["borrado", "redactado", "conservado",
                    "delegado", "bloqueado"]
    filas: int
    dueno: str
    plazo_dias: int | None
    base: str | None               # por qué se queda lo que queda


class MemoryDeletionReceipt(BaseModel):
    """Que la operación distribuida se ejecutó: un almacén por
    fila. `completo` es False mientras quede uno pendiente."""
    solicitud: str
    sujeto: str
    motivo: str
    ejecutado_por: str
    ts: datetime
    almacenes: list[AlmacenBorrado]
    completo: bool
    pendientes: list[str]


def conectar(autocommit=True):
    return psycopg.connect(DB, autocommit=autocommit,
                           row_factory=dict_row,
                           options="-c search_path=banco,public")


def sin_personal(campos: dict) -> None:
    """La negativa del `atributos` del 36.6 en la otra punta:
    allí muere la traza, aquí la escritura."""
    sucios = sorted(k for k, v in campos.items()
                    if PERSONAL.search(str(v)))
    if sucios:
        raise MemoriaRechazada(
            f"dato personal en {sucios} (34.6, hábito 1)")


def existe(cur, tabla: str) -> bool:
    cur.execute("SELECT to_regclass(%s) IS NOT NULL AS hay",
                (tabla,))
    return cur.fetchone()["hay"]


# --- anadido del M34.7 (extraer_banco) ---
# 
ESCRIBIR = """
INSERT INTO banco.memoria (tipo, namespace, clave, valor, sujeto,
    sensibilidad, confianza, consent_basis, owner, source_run_id,
    evidencia, aprobado_por, propuesta_id, expira_en)
SELECT %(tipo)s, %(ns)s, %(clave)s, %(valor)s, %(sujeto)s,
    %(sens)s, 1.0, %(base)s, dueno, %(run)s, %(evid)s,
    %(firma)s, %(prop)s, caduca_memoria(%(tipo)s, now())
  FROM banco.ttl_memoria WHERE tipo = %(tipo)s
ON CONFLICT (namespace, clave) DO UPDATE
   SET valor = EXCLUDED.valor, evidencia = EXCLUDED.evidencia,
       source_run_id = EXCLUDED.source_run_id, creado_en = now(),
       expira_en = EXCLUDED.expira_en
RETURNING *
"""
CUENTA = ("SELECT count(*) AS n FROM banco.memoria WHERE"
          " namespace = %s")
ANOTAR = """
INSERT INTO banco.supresiones (solicitud, sujeto, almacen, tablas,
    accion, filas, dueno, plazo_dias, base, ejecutado_por)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (solicitud, almacen) DO UPDATE
   SET accion = EXCLUDED.accion, filas = EXCLUDED.filas,
       base = EXCLUDED.base, ts = now()
"""


def parte(i, tablas, accion, filas, dueno, plazo=0, base=None):
    """Una de las siete filas del receipt de supresión."""
    return AlmacenBorrado(almacen=SIETE[i], tablas=tablas,
                          accion=accion, filas=filas, dueno=dueno,
                          plazo_dias=plazo, base=base)


def _escrito(f: dict) -> MemoryWriteReceipt:
    ns = tuple(f["namespace"])
    return MemoryWriteReceipt(
        namespace=ns, clave=f["clave"], tipo=f["tipo"],
        owner=f["owner"], sensibilidad=f["sensibilidad"],
        consent_basis=f["consent_basis"], evidencia=f["evidencia"],
        source_run_id=f["source_run_id"], creado_en=f["creado_en"],
        aprobado_por=f["aprobado_por"], expira_en=f["expira_en"],
        revertir=f"olvidar_memoria({ns}, {f['clave']!r},"
                 f" 'user_request')")


def recordar_preferencia_cliente(
        cliente_id: str,
        clave: Literal["idioma", "canal_preferido",
                       "formato_resumen"],
        valor: str, evidencia: str) -> MemoryWriteReceipt:
    """El primer @tool del 34.5. El `owner` no lo elige quien
    llama: sale del `ttl_memoria`, con su TTL al lado."""
    if clave not in CLAVES:
        raise MemoriaRechazada(f"clave fuera de catálogo: {clave}")
    sin_personal({"valor": valor, "evidencia": evidencia})
    with conectar() as cx, cx.cursor() as cur:
        cur.execute(ESCRIBIR, {
            "tipo": "individual", "clave": clave,
            "ns": [TENANT, "preferencias", cliente_id],
            "sujeto": cliente_id, "sens": "confidential",
            "valor": json.dumps({"valor": valor}),
            "base": CONSENTIMIENTO, "run": CTX()["run"],
            "evid": evidencia, "firma": None, "prop": None})
        return _escrito(cur.fetchone())


def proponer_memoria_colectiva(
        dominio: str,
        tipo: Literal["faq", "eval_case", "playbook",
                      "policy_candidate"],
        resumen: str,
        evidencias_run_ids: list[str]) -> MemoryProposalReceipt:
    """El segundo @tool del 34.5. No escribe en el namespace
    colectivo: abre una fila en la cola del 35.6 y se va."""
    if tipo not in TIPOS:
        raise MemoriaRechazada(f"tipo no propuesto: {tipo}")
    if not evidencias_run_ids:
        raise MemoriaRechazada("candidato sin evidencias (34.3)")
    sin_personal({"resumen": resumen})
    ctx = CTX()
    h = ctx.get("humano")
    # La misma línea que el `decidir` del 37.2, y por el mismo
    # motivo: `propone` es una columna `text NOT NULL` y el lote
    # nocturno del 11.5 no trae humano ninguno, así que la clase
    # va delante y ese caso llega a la cola como carga de trabajo
    # en lugar de reventar el INSERT con un `None`.
    propone = (f"human:{h['id']}" if h
               else f"workload:{ctx['agente']['id']}")
    # La referencia es la clave de NEGOCIO del candidato, así que
    # proponer dos veces lo mismo no abre una segunda fila.
    ref = "mem-" + hashlib.sha256(
        f"{dominio}|{tipo}|{resumen}".encode()).hexdigest()[:12]
    ns = [TENANT, "colectiva", dominio]
    with conectar() as cx, cx.cursor() as cur:
        cur.execute("SELECT DISTINCT traza FROM banco.registro_ia"
                    " WHERE traza = ANY(%s)",
                    (list(evidencias_run_ids),))
        vistas = {f["traza"] for f in cur.fetchall()}
        faltan = [r for r in evidencias_run_ids if r not in vistas]
        if faltan:
            raise MemoriaRechazada(f"sin traza: {faltan} (34.3)")
        cur.execute(CUENTA, (ns,))
        antes = cur.fetchone()["n"]
    pid = hitl.encolar(
        hilo=f"memoria|{ref}", run=ctx["run"], agente=ctx["agente"],
        accion="memoria.publicar",
        propone=propone,
        propuesta={"referencia": ref, "dominio": dominio,
                   "tipo": tipo, "resumen": resumen,
                   "evidencias_run_ids": list(evidencias_run_ids)})
    with conectar() as cx, cx.cursor() as cur:
        cur.execute(CUENTA, (ns,))
        despues = cur.fetchone()["n"]
    return MemoryProposalReceipt(
        referencia=ref, dominio=dominio, tipo=tipo,
        propuesta_id=pid, hilo=f"memoria|{ref}", publicado=False,
        evidencias_run_ids=list(evidencias_run_ids),
        colectivas_antes=antes, colectivas_despues=despues,
        estado="pendiente")


def publicar(receipt: dict) -> MemoryWriteReceipt | None:
    """El aprendizaje controlado, cobrado. Devuelve None si el
    steward rechazó, y no levanta excepción: es el `reanudar` de
    `hitl.aprobar`, y una excepción aquí desharía la decisión."""
    with conectar() as cx, cx.cursor() as cur:
        cur.execute("SELECT propuesta FROM banco.aprobaciones"
                    " WHERE id = %s", (receipt["propuesta_id"],))
        fila = cur.fetchone()
    if fila is None:
        raise hitl.ReciboInvalido("publicar: propuesta ausente")
    p = fila["propuesta"]
    # La firma la comprueba el 35.6: `encolar` con `receipt`
    # recalcula la huella y revienta si el recibo no salió de esa
    # cola o si lo firmó quien lo propuso.
    hitl.encolar(hilo=receipt["hilo"], run=receipt["run"],
                 agente={"id": receipt["agente"],
                         "version": receipt["version"]},
                 propone=receipt["propone"], propuesta=p,
                 receipt=receipt)
    if receipt["decision"] == "reject":
        return None
    with conectar() as cx, cx.cursor() as cur:
        cur.execute(ESCRIBIR, {
            "tipo": "collective", "clave": p["referencia"],
            "ns": [TENANT, "colectiva", p["dominio"]],
            "sujeto": None, "valor": json.dumps(p),
            "sens": "internal", "base": None,
            "run": receipt["run"], "firma": receipt["aprobador"],
            "evid": ",".join(p["evidencias_run_ids"]),
            "prop": receipt["propuesta_id"]})
        return _escrito(cur.fetchone())


def reanudar(hilo: str, cmd, fila) -> None:
    """Lo que la consola del steward le pasa a `hitl.aprobar`:
    aquí no hay grafo que reanudar, hay memoria que publicar."""
    if hilo.startswith("memoria|"):
        publicar(cmd.resume)


def olvidar_memoria(
        namespace: tuple[str, ...], key: str,
        motivo: Literal["user_request", "expired", "incorrect",
                        "policy"]) -> MemoryDeletionReceipt:
    """El tercer @tool del 34.5. Toca UN almacén de los siete y el
    receipt lo dice. Una clave que no existe devuelve cero filas y
    no revienta: una solicitud repetida entra a diario."""
    ns, pre = list(namespace), ".".join(namespace)
    with conectar(autocommit=False) as cx, cx.cursor() as cur:
        cur.execute("DELETE FROM banco.memoria WHERE namespace ="
                    " %s AND clave = %s RETURNING sujeto",
                    (ns, key))
        filas = cur.fetchall()
        n = len(filas)
        if existe(cur, "store"):
            cur.execute("DELETE FROM store WHERE prefix = %s AND"
                        " key = %s", (pre, key))
            n += cur.rowcount
        p = parte(0, ["banco.memoria", "store"], "borrado", n,
                  "DPO")
        sujeto = (filas[0]["sujeto"] if filas else None) or pre
        cur.execute(ANOTAR, (f"olvido:{pre}:{key}", sujeto,
                             p.almacen, p.tablas, p.accion, n,
                             p.dueno, 0, None,
                             "tool:olvidar_memoria"))
        cur.execute("SELECT now() AS t")
        ts = cur.fetchone()["t"]
    return MemoryDeletionReceipt(
        solicitud=f"olvido:{pre}:{key}", motivo=motivo, ts=ts,
        sujeto=sujeto, ejecutado_por="tool:olvidar_memoria",
        almacenes=[p], completo=False,
        pendientes=list(SIETE[1:]))


def purgar_caducadas() -> dict[str, int]:
    """El TTL cobrado. Sin este bucle en el batch nocturno del
    11.5, `expira_en` es una columna decorativa."""
    cuenta: dict[str, int] = {}
    with conectar(autocommit=False) as cx, cx.cursor() as cur:
        cur.execute("DELETE FROM banco.memoria WHERE expira_en <"
                    " now() RETURNING tipo, clave,"
                    " array_to_string(namespace, '.') AS pre")
        for f in cur.fetchall():
            cuenta[f["tipo"]] = cuenta.get(f["tipo"], 0) + 1
            cur.execute("DELETE FROM store WHERE prefix = %s AND"
                        " key = %s", (f["pre"], f["clave"]))
    return cuenta
