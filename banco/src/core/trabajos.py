# src/core/trabajos.py --- la cola con leases del 21.1: reclamo con
# recuperación de leases vencidos, backoff con jitter, dead letter
# y compensación de saga. El worker del 11.5 deja de elegir su lote
# con un SELECT propio y se lo pide aquí. Cursores con
# `row_factory=dict_row`, como el pool del 32.2.
import json
import random
from datetime import timedelta

LEASE = 300        # s; ha de superar al paso más lento del grafo
MAX_INTENTOS = 5   # al sexto reclamo, dead_letter
BASE = 20          # s; topes de espera 20, 40, 80, 160, 320
TECHO = 3600       # s; el backoff no crece más allá de una hora

RECLAMO = """
UPDATE banco.trabajos
   SET estado = 'leased', worker = %(worker)s,
       intentos = intentos + 1,
       lease_hasta = now() + make_interval(secs => %(lease)s)
 WHERE id = (
     SELECT id FROM banco.trabajos
      WHERE (estado IN ('pending', 'retry_scheduled')
             AND correr_tras <= now())
         -- La línea del Ejercicio 21.1: el lease vencido vuelve a
         -- la cola sin que nadie declare muerto al que lo tenía.
         OR (estado = 'leased' AND lease_hasta < now())
      ORDER BY prioridad DESC, creado_en
        FOR UPDATE SKIP LOCKED
      LIMIT 1)
RETURNING *
"""


def encolar(cur, tipo: str, clave: str, carga: dict, prioridad=0):
    """`clave` es la de NEGOCIO (la referencia, no un uuid): el
    índice parcial del DDL la usa para que reencolar un caso vivo
    no abra un segundo trabajo."""
    cur.execute(
        "INSERT INTO banco.trabajos (tipo, clave, carga, prioridad)"
        " VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"
        " RETURNING id", (tipo, clave, json.dumps(carga), prioridad))
    fila = cur.fetchone()
    return fila["id"] if fila else None


def claim_next_job(cur, worker: str, lease: int = LEASE):
    """El del 21.2, ya no conceptual. Cuenta el intento al
    RECLAMAR y no al fallar, así el caso que mata al worker antes
    de escribir nada llega igual a dead_letter."""
    cur.execute(RECLAMO, {"worker": worker, "lease": lease})
    return cur.fetchone()


def renovar(cur, job: dict, lease: int = LEASE):
    """Entre paso y paso. False = otro robó el lease y hay que
    abandonar el caso sin escribir una línea más."""
    cur.execute(
        "UPDATE banco.trabajos SET lease_hasta ="
        " now() + make_interval(secs => %s) WHERE id = %s"
        " AND worker = %s AND estado IN ('leased', 'running')",
        (lease, job["id"], job["worker"]))
    return cur.rowcount == 1


def en_marcha(cur, job_id: int):
    cur.execute("UPDATE banco.trabajos SET estado='running'"
                " WHERE id=%s", (job_id,))


def esperar_humano(cur, job_id: int):
    """Suelta lease y worker: un caso en aprobación no ocupa un
    proceso ni caduca como si se hubiera muerto el que lo tenía."""
    cur.execute("UPDATE banco.trabajos SET estado='waiting_human',"
                " worker=NULL, lease_hasta=NULL WHERE id=%s",
                (job_id,))


def despertar(cur, job_id: int):
    """La aprobación lo devuelve a la cola con su thread_id
    intacto; lo reanuda el worker que lo reclame."""
    cur.execute("UPDATE banco.trabajos SET estado='pending',"
                " correr_tras=now() WHERE id=%s AND"
                " estado='waiting_human'", (job_id,))
    return cur.rowcount == 1


def completar(cur, job_id: int, resultado: dict):
    cur.execute("UPDATE banco.trabajos SET estado='completed',"
                " worker=NULL, lease_hasta=NULL, resultado=%s"
                " WHERE id=%s", (json.dumps(resultado), job_id))


def espera(intentos: int) -> timedelta:
    """Jitter COMPLETO, uniforme en [0, tope]: los cien trabajos
    caídos por la misma indisponibilidad del core vuelven
    repartidos y no todos juntos a los veinte segundos."""
    tope = min(BASE * 2 ** (intentos - 1), TECHO)
    return timedelta(seconds=random.uniform(0, tope))


def fallar(cur, job: dict, error: str) -> str:
    """Devuelve el estado en que queda, que es lo que cuenta el
    informe del worker. La hora futura la pone Postgres."""
    if job["intentos"] >= MAX_INTENTOS:
        cur.execute("UPDATE banco.trabajos SET estado='dead_letter',"
                    " error=%s, worker=NULL, lease_hasta=NULL"
                    " WHERE id=%s", (error[:500], job["id"]))
        return "dead_letter"
    cur.execute("UPDATE banco.trabajos SET estado='retry_scheduled',"
                " error=%s, worker=NULL, lease_hasta=NULL,"
                " correr_tras=now() + %s WHERE id=%s",
                (error[:500], espera(job["intentos"]), job["id"]))
    return "retry_scheduled"


COMPENSACIONES = {}   # paso -> quién lo deshace


def compensacion(paso: str):
    """Un paso sin entrada aquí revienta en `compensar`, y es
    deliberado: la saga del 21.3 se rompe al escribirla."""
    def registrar(fn):
        COMPENSACIONES[paso] = fn
        return fn
    return registrar


def anotar_efecto(cur, job_id: int, paso: str, datos: dict):
    """En la misma transacción que el efecto si es interno, y
    ANTES de la llamada si es externo: lo anotado que no llegó a
    ocurrir se compensa en vano, y lo ocurrido sin anotar no lo
    deshace nadie."""
    cur.execute("INSERT INTO banco.efectos (trabajo_id, paso, datos)"
                " VALUES (%s, %s, %s)",
                (job_id, paso, json.dumps(datos)))


def compensar(cur, job_id: int) -> list[str]:
    """Deshace en orden INVERSO. Cada compensación se marca en su
    misma transacción y aun así ha de poder repetirse: si el
    proceso cae entre el efecto y la marca, vuelve a llamarse."""
    cur.execute("SELECT id, paso, datos FROM banco.efectos"
                " WHERE trabajo_id=%s AND compensado_en IS NULL"
                " ORDER BY id DESC FOR UPDATE", (job_id,))
    hechas = []
    for e in cur.fetchall():
        COMPENSACIONES[e["paso"]](cur, e["datos"])
        cur.execute("UPDATE banco.efectos SET compensado_en=now()"
                    " WHERE id=%s", (e["id"],))
        hechas.append(e["paso"])
    return hechas


@compensacion("marcar_propuesta")
def _rechazar(cur, d):
    cur.execute("UPDATE banco.incidencias SET estado='abierta',"
                " cola=NULL WHERE referencia=%s AND"
                " estado='escalada'", (d["referencia"],))


@compensacion("bloquear_tarjeta")
def _desbloquear(cur, d):
    """Compensar en el core es pedir lo contrario, y esa petición
    también falla: entra en esta cola con su backoff."""
    encolar(cur, "desbloquear_tarjeta", f"desbloq-{d['tarjeta']}",
            {"tarjeta": d["tarjeta"], "motivo": "compensacion"},
            prioridad=10)
