# src/core/hitl.py --- el servicio de aprobaciones del 35.4. La cola
# vive en `banco.aprobaciones`: una fila por PROPUESTA, con su
# receipt firmado. El TRABAJO lo guarda el `trabajos.py` del 21.5 y
# la PAUSA el checkpoint del 5.2, y hacen falta los tres. Cursores
# con `row_factory=dict_row`, como el pool del 32.2.
import hashlib
import hmac
import json
import logging
import os

import psycopg
from langgraph.types import Command                    # el 6.1
from psycopg.rows import dict_row

DB = os.environ["DATABASE_URL"]
SLA = 24            # h sin contestar; `caducar` rechaza, no borra
ESTADOS = {"approve": "aprobada", "edit": "editada",
           "reject": "rechazada"}
log = logging.getLogger("hitl")


class AutoAprobacion(Exception):
    """Maker-checker: quien propone no firma (35.4)."""


class ReciboInvalido(Exception):
    """Un `Command(resume=...)` que no salió de esta cola."""


def _sin_consola(hilo, cmd, fila):
    raise RuntimeError(f"hitl: nadie reanuda {hilo} (37.2)")


REANUDAR = _sin_consola      # lo pone la consola, no este fichero


def _cx():
    return psycopg.connect(DB, autocommit=True, row_factory=dict_row)


def _canon(dato) -> str:
    """Mismo dict, misma cadena. Sin esto, dos órdenes de claves dan
    dos huellas y dos firmas de lo mismo."""
    return json.dumps(dato, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)


def _huella(accion: str, propuesta: dict) -> str:
    return hashlib.sha256(
        _canon([accion, propuesta]).encode()).hexdigest()[:32]


def _firmar(recibo: dict) -> str:
    """HMAC sobre el receipt entero, con la clave del broker del
    35.3. Sin clave no se aprueba nada, que es el `por_defecto` del
    26.2 aplicado aquí."""
    clave = os.environ["HITL_CLAVE"].encode()
    limpio = {k: v for k, v in recibo.items() if k != "firma"}
    return hmac.new(clave, _canon(limpio).encode(),
                    hashlib.sha256).hexdigest()


def _diff(propuesta: dict, args) -> dict:
    """El diff del receipt, clave a clave: lo que hay que poder
    reconstruir seis meses después es qué cambió y de qué a qué."""
    if args is None:
        return {}
    return {k: [propuesta.get(k), args.get(k)]
            for k in sorted(set(propuesta) | set(args))
            if propuesta.get(k) != args.get(k)}


def encolar(*, hilo, run, agente, propone, propuesta, accion=None,
            receipt=None) -> int:
    """Las dos mitades del ciclo en una firma, porque el `decidir`
    del 37.2 la llama con `receipt` y quien publica la pausa la
    llama sin él. Sin receipt abre la propuesta y la deja
    `pendiente`, que es lo que lista `pendientes`. Con receipt no
    abre nada: comprueba que quien reanuda trae la firma de esta
    cola, y revienta si no."""
    accion = accion or (receipt or {}).get("accion")
    huella = _huella(accion, propuesta)
    with _cx() as cx, cx.cursor() as cur:
        if receipt is not None:
            return _verificar(cur, hilo, huella, propone, receipt)
        cur.execute(
            "INSERT INTO banco.aprobaciones (hilo, huella, run_id,"
            " agente, version, accion, propuesta, propone) VALUES"
            " (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (hilo, huella)"
            " WHERE estado='pendiente' DO NOTHING RETURNING id",
            (hilo, huella, run, agente["id"], agente["version"],
             accion, json.dumps(propuesta), propone))
        fila = cur.fetchone()
        if fila is not None:
            return fila["id"]
        # La misma propuesta del mismo hilo no abre una segunda
        # fila mientras la primera siga viva, y el índice parcial
        # que lo impide es el de la cola del 21.5.
        cur.execute("SELECT id FROM banco.aprobaciones WHERE hilo=%s"
                    " AND huella=%s AND estado='pendiente'",
                    (hilo, huella))
        return cur.fetchone()["id"]


def _verificar(cur, hilo, huella, propone, receipt) -> int:
    """La comprobación que hace que la firma sirva de algo.
    `Command(resume=...)` no lo autentica nadie: quien alcance el
    checkpointer reanuda el hilo que quiera con un `{"decision":
    "approve"}` escrito a mano, y el `decidir` del 37.2 se lo cree.
    Esto lo para, y lo para antes del commit, porque la excepción
    sube por `decidir` y se lleva el turno."""
    cur.execute("SELECT * FROM banco.aprobaciones WHERE id=%s",
                (receipt.get("propuesta_id"),))
    fila = cur.fetchone()
    if (fila is None or fila["hilo"] != hilo
            or fila["huella"] != huella):
        raise ReciboInvalido(f"{hilo}: receipt de otra propuesta")
    if fila["estado"] == "pendiente":
        raise ReciboInvalido(f"{hilo}: nadie decidió esa propuesta")
    if receipt.get("firma") != fila["firma"]:
        raise ReciboInvalido(f"{hilo}: firma ajena a la fila")
    if _firmar(receipt) != receipt["firma"]:
        raise ReciboInvalido(f"{hilo}: receipt manipulado")
    if receipt.get("aprobador") == propone:
        raise AutoAprobacion(f"{propone} firmó su propia propuesta")
    return fila["id"]


def pendientes(agente=None, limite=50) -> list[dict]:
    """La pantalla del 35.4, una para los cuatro agentes, ordenada
    por antigüedad. La edad la calcula Postgres, por el mismo motivo
    que el `ts` del receipt."""
    with _cx() as cx, cx.cursor() as cur:
        cur.execute(
            "SELECT id, hilo, agente, version, accion, propuesta,"
            " propone, creado_en, extract(epoch FROM now() -"
            " creado_en)/3600 AS edad_h FROM banco.aprobaciones"
            " WHERE estado='pendiente' AND (%s::text IS NULL"
            " OR agente=%s) ORDER BY creado_en LIMIT %s",
            (agente, agente, limite))
        return cur.fetchall()


def _receipt(cur, fila, decision, aprobador, args, motivo) -> dict:
    """Quién, cuándo y el diff de lo aprobado contra lo propuesto.
    El `now()` lo da Postgres: los cuatro procesos del 37.2 no
    comparten reloj y un receipt se lee ordenado por hora."""
    cur.execute("SELECT now() AS t")
    recibo = {"propuesta_id": fila["id"], "hilo": fila["hilo"],
              "run": fila["run_id"], "agente": fila["agente"],
              "version": fila["version"], "accion": fila["accion"],
              "propone": fila["propone"], "aprobador": aprobador,
              "decision": decision, "motivo_rechazo": motivo,
              "diff": _diff(fila["propuesta"], args),
              "ts": cur.fetchone()["t"].isoformat()}
    if args is not None:
        recibo["args"] = args        # el commit va con estos
    recibo["firma"] = _firmar(recibo)
    return recibo


def _cerrar(cur, fila, estado, recibo) -> bool:
    """El `WHERE estado='pendiente'` desempata a los dos aprobadores
    que abrieron la misma pantalla: gana el primero y el segundo se
    lleva un `rowcount` 0, como el `despertar` del 21.5."""
    cur.execute(
        "UPDATE banco.aprobaciones SET estado=%s, aprobador=%s,"
        " decidido_en=%s, diff=%s, motivo=%s, firma=%s WHERE id=%s"
        " AND estado='pendiente'",
        (estado, recibo["aprobador"], recibo["ts"],
         json.dumps(recibo["diff"]), recibo["motivo_rechazo"],
         recibo["firma"], fila["id"]))
    return cur.rowcount == 1


def _decidir(id_prop, aprobador, decision, args=None, motivo=None,
             reanudar=None) -> dict:
    with _cx() as cx, cx.cursor() as cur:
        cur.execute("SELECT * FROM banco.aprobaciones WHERE id=%s"
                    " AND estado='pendiente'", (id_prop,))
        fila = cur.fetchone()
        if fila is None:
            raise ReciboInvalido(f"{id_prop}: decidida o inexistente")
        if decision != "reject" and aprobador == fila["propone"]:
            # El intento se va al log. La fila es el libro de
            # decisiones, y una firma rechazada nunca llegó a
            # serlo. Y mira en una sola dirección: exigir dos
            # humanos para decir «no» es lo que llena la cola.
            log.warning("hitl: %s firma su propuesta %s (35.4)",
                        aprobador, id_prop)
            raise AutoAprobacion(f"{aprobador} propuso la {id_prop}")
        recibo = _receipt(cur, fila, decision, aprobador, args, motivo)
        if not _cerrar(cur, fila, ESTADOS[decision], recibo):
            raise ReciboInvalido(f"{id_prop}: la decidió otro")
        # Y ahora la pausa: el hilo del 18.3, jamás el run. Quien
        # reanuda pone de vuelta al humano de `fila["propone"]`, que
        # es el dato que la traza del 36.6 no puede llevar.
        (reanudar or REANUDAR)(fila["hilo"], Command(resume=recibo),
                               fila)
    return recibo


def aprobar(id_prop, aprobador, args=None, reanudar=None) -> dict:
    """`args` distinto de None es el «edit before commit» del 35.4:
    dos filas de aquella tabla y una sola función, y el diff del
    receipt es lo que las separa en la auditoría."""
    return _decidir(id_prop, aprobador,
                    "approve" if args is None else "edit",
                    args=args, reanudar=reanudar)


def rechazar(id_prop, aprobador, motivo, reanudar=None) -> dict:
    return _decidir(id_prop, aprobador, "reject", motivo=motivo,
                    reanudar=reanudar)


def caducar(sla=SLA, reanudar=None) -> list[int]:
    """La fila que nadie miró, que es lo que le falta a toda cola
    de aprobaciones. Caducar contesta la pausa con un rechazo
    firmado y deja la fila donde está, porque una propuesta sin
    contestar deja el grafo parado para siempre y el trabajo del
    21.5 en `waiting_human`, sin lease, sin worker y sin nadie que
    lo cuente. Aquí firma el sistema, y la fila dice que fue él."""
    caducadas = []
    with _cx() as cx, cx.cursor() as cur:
        cur.execute("SELECT * FROM banco.aprobaciones WHERE"
                    " estado='pendiente' AND creado_en < now() -"
                    " make_interval(hours => %s)", (sla,))
        for fila in cur.fetchall():
            recibo = _receipt(cur, fila, "reject", "sistema:sla",
                              None, f"sin contestar en {sla} h")
            if _cerrar(cur, fila, "caducada", recibo):
                (reanudar or REANUDAR)(
                    fila["hilo"], Command(resume=recibo), fila)
                caducadas.append(fila["id"])
    return caducadas
