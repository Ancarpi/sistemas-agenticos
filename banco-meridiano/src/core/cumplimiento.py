# cumplimiento.py --- los dos artículos que se implementan igual
# en todos los canales: el aviso del 50 y el registro del 12.
import hashlib
import json
import os
from datetime import datetime, timezone

from psycopg_pool import ConnectionPool

POOL = ConnectionPool(os.environ["DATABASE_URL"], open=True)
VERSION_AVISO = "2026-08-02"   # el día en que el 50 fue exigible

AVISOS = {
    # 50(1): «hablas con una IA». Los canales con humano delante.
    "chat": ("Hablas con un asistente automático de Banco "
             "Meridiano: no es una persona. Puede equivocarse, y "
             "no decide nada sobre tu dinero por sí mismo. "
             "Escribe «quiero hablar con una persona» y te paso "
             "con el equipo."),
    "voz": ("Le atiende el asistente virtual de Banco Meridiano. "
            "Soy una inteligencia artificial y la llamada se "
            "graba. ¿En qué puedo ayudarle?"),
    # 50(1) y, por ser contenido generado, el marcado del 50(2).
    # NO es 50(4): el Art. 3(60) reserva el «deep fake» al
    # parecido con una persona o un hecho que existen, y esta
    # cara no es la de nadie. Si fuera la de una persona real
    # --- el caso del 14.5 y sus derechos de imagen ---, sí.
    "avatar": ("Le atiende el asistente virtual de Banco "
               "Meridiano. Soy una inteligencia artificial: la "
               "cara y la voz están generadas por ordenador. La "
               "sesión se graba. ¿En qué puedo ayudarle?"),
}
# El hilo de Slack del 12.6 lleva el MISMO texto que el chat web
# y es otra superficie. El texto se comparte; el canal, no.
AVISOS["slack"] = AVISOS["chat"]


def anotar(tipo: str, canal: str, sujeto: str, cur=None,
           traza: str | None = None, **detalle) -> None:
    """Art. 12: se guarda el HECHO, nunca el contenido. `sujeto` es
    un identificador --- cliente o sala ---, jamás un nombre ni un
    IBAN: este es el único almacén del 34.6 que no se puede borrar,
    así que es el único donde no se puede escribir el dato. Con
    `cur`, la fila entra en la transacción de quien llama y se
    deshace con ella; sin él, abre la suya y le sobrevive."""
    sql = ("INSERT INTO meridiano.registro_ia"
           " (ts, tipo, canal, sujeto, traza, detalle)"
           " VALUES (%s, %s, %s, %s, %s, %s)")
    args = (datetime.now(timezone.utc), tipo, canal, sujeto,
            traza, json.dumps(detalle, ensure_ascii=False))
    if cur is not None:
        cur.execute(sql, args)
        return
    with POOL.connection() as bd:
        bd.execute(sql, args)


def anotar_aviso(canal: str, sujeto: str, **extra) -> None:
    """DESPUÉS de entregarlo, nunca antes: anotar la intención de
    avisar fabrica un registro que dice que cumpliste el día que no
    cumpliste. Se guarda la firma del texto y no el texto."""
    firma = hashlib.sha256(AVISOS[canal].encode()).hexdigest()
    anotar("art50_aviso", canal, sujeto,
           version=VERSION_AVISO, sha256=firma[:16], **extra)
