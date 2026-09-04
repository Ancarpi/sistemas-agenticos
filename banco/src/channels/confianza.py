# src/channels/confianza.py --- lo que un canal tiene que emitir
# para que el usuario pueda confiar: el aviso, el progreso, las
# citas y el traspaso. El transporte es el servidor.py del 12.5.
import asyncio
import re
import time
from typing import Literal

from pydantic import BaseModel

from cumplimiento import AVISOS, POOL, anotar, anotar_aviso
from src.rag.gobierno import procedencia   # las fichas del 24.6
from src.rag.hibrida import NIVELES

LATIDO = 4.0       # s de silencio antes de volver a decir algo
SLA_TURNO = 25.0   # s tras los cuales el turno deja de ser síncrono
CITA = re.compile(r"\[(\d{1,2})\]")
DIFERIDO = ("Sigo con ello, pero tarda más de lo normal. Te dejo "
            "aquí la respuesta en cuanto la tenga.")
PROXIMA = {   # el humano abre el caso con una propuesta, no en blanco
    "user_requested": "Llamar al cliente; el caso está al día.",
    "low_confidence": "Confirmar la categoría y cerrar o devolver.",
    "complaint": "Abrir reclamación formal con el plazo del SLA.",
    "sensitive_action": "Aprobar o rechazar la acción propuesta.",
    "tool_failure": "Consultar el core a mano y responder.",
    "policy": "Resolver fuera del ámbito del asistente.",
}


class Cita(BaseModel):
    """Fuente, versión y vigencia salen de la FILA; del texto del
    modelo solo sale el número entre corchetes. La vigencia es
    `caduca` (24.6) y nunca la columna `fecha`, que es la de
    redacción del documento."""
    indice: int
    fuente: str
    seccion: str | None
    version: int
    caduca: str


class HumanHandoffPacket(BaseModel):
    """El del 22.3, tal cual: lo que falta allí es quién lo llena."""
    conversation_id: str
    customer_id: str | None
    reason: Literal[
        "low_confidence", "policy", "user_requested",
        "complaint", "sensitive_action", "tool_failure"
    ]
    verified_facts: list[str]
    unresolved_questions: list[str]
    tools_used: list[str]
    proposed_next_action: str
    risk_flags: list[str]
    trace_url: str | None


async def abrir(canal: str, sujeto: str):
    """Sustituye a la constante AVISO del 12.5. `anotar_aviso` es
    E/S bloqueante (de ahí el `to_thread`) y va DESPUÉS de haberlo
    entregado, nunca antes: es la regla del 16.5."""
    yield {"tipo": "aviso", "texto": AVISOS[canal]}
    await asyncio.to_thread(anotar_aviso, canal, sujeto)


async def con_latido(cola: asyncio.Queue):
    """El `while` del flujo() del 12.5 con la única señal de
    progreso que no miente: la última etapa REAL y cuánto lleva
    esperando. Las etapas las emite el grafo (6.3); aquí no se
    inventa ninguna, que es lo que el 22.2 llama teatro."""
    inicio = visto = time.monotonic()
    etapa = "Preparando la consulta..."
    while True:
        try:
            ev = await asyncio.wait_for(cola.get(), LATIDO)
        except TimeoutError:
            if time.monotonic() - inicio > SLA_TURNO:
                # No se cancela nada: la tarea del 12.5 es DUEÑA
                # del grafo, termina, guarda, y el cliente lo lee
                # en /ultimo. Cortar aquí tira un turno pagado.
                yield {"tipo": "diferido", "texto": DIFERIDO}
                return
            yield {"tipo": "espera", "texto": etapa,
                   "segundos": round(time.monotonic() - visto)}
            continue
        if ev is None:
            return
        visto = time.monotonic()
        if ev["tipo"] == "actividad":
            etapa = ev["texto"]
        yield ev
