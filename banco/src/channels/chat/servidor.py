# servidor.py --- el transporte, y nada más: el cerebro es el
# canal_chat() del 6.3, importado tal cual y sin tocar.
import asyncio
import json
import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from canal_chat import canal_chat            # el generador del 6.3
from grafo_conciliacion import obtener_app   # la fábrica del 5.3

api = FastAPI()
# asyncio solo guarda referencias DÉBILES a sus tareas: sin este
# set, el recolector puede llevarse una a medio ejecutar.
VIVAS: set[asyncio.Task] = set()

# Art. 50, literal y copiable. Cambia el responsable y ya está.
AVISO = ("Hablas con un asistente automático del banco: "
         "no es una persona. Puede equivocarse, y no decide nada "
         "sobre tu dinero por sí mismo.")


class Turno(BaseModel):
    pregunta: str
    referencia: str


def config(cliente_id: str) -> dict:
    return {"configurable": {"thread_id": f"cliente:{cliente_id}"}}


def sse(evento: dict) -> str:
    # json.dumps SIEMPRE: un \n suelto en el texto parte el evento
    # en dos y el navegador se come la mitad sin avisar.
    return "data: " + json.dumps(evento, ensure_ascii=False) + "\n\n"


async def correr(hilo: str, turno: Turno, cola: asyncio.Queue):
    # El finally es la diferencia entre un fallo y un spinner
    # eterno: si canal_chat revienta --- timeout del modelo, RAG
    # caído, el core que no contesta --- y nadie pone el centinela,
    # flujo() se queda en `await cola.get()` para siempre.
    try:
        async for ev in canal_chat(turno.pregunta,
                                   turno.referencia, hilo):
            await cola.put(ev)
    except Exception as fallo:
        # Se registra y no se relanza: a esta tarea no la espera
        # nadie, así que un raise aquí no aborta nada --- solo deja
        # el «Task exception was never retrieved» que nadie lee.
        logging.exception("turno roto en el hilo %s", hilo)
        await cola.put({"tipo": "error", "texto": str(fallo)})
    finally:
        await cola.put(None)


@api.post("/chat/{cliente_id}")
async def chat(cliente_id: str, turno: Turno):
    # AQUÍ, y en ningún otro sitio, se decide la identidad de la
    # conversación: un grafo, miles de clientes, un hilo cada uno.
    # OJO: tal cual, el cliente_id viene del path y cualquiera
    # escribe en el hilo de otro. En producción sale del token de
    # sesión (Depends), NUNCA de la URL. Es el IDOR del M16.
    hilo = f"cliente:{cliente_id}"
    cola: asyncio.Queue = asyncio.Queue()
    # Compilar el grafo es del 5.3 y de su loop, no de aquí; y la
    # lectura del estado va con `aget_state`: la síncrona, dentro
    # de un `async def`, lanza InvalidStateError.
    grafo = await obtener_app()
    # El Art. 50 pide el aviso en el PRIMER contacto, no en cada
    # turno: si el hilo ya tiene checkpoint, no se reemite.
    nuevo = not (await grafo.aget_state(config(cliente_id))).values
    # create_task, no await: la tarea es DUEÑA del grafo y sobrevive
    # a la conexión. Con el grafo dentro del generador de abajo,
    # cerrar la pestaña lo mata a medias.
    tarea = asyncio.create_task(correr(hilo, turno, cola))
    VIVAS.add(tarea)
    tarea.add_done_callback(VIVAS.discard)

    async def flujo():
        if nuevo:
            yield sse({"tipo": "aviso", "texto": AVISO})
        while (ev := await cola.get()) is not None:
            yield sse(ev)
        yield sse({"tipo": "fin"})

    # Sin estas dos cabeceras, nginx bufferea el flujo entero y el
    # usuario recibe los cuarenta tokens de golpe, al final.
    return StreamingResponse(
        flujo(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache",
                 "X-Accel-Buffering": "no"})


@api.get("/chat/{cliente_id}/ultimo")
async def ultimo(cliente_id: str):
    # El flujo no es la fuente de verdad; el checkpoint lo es (6.3).
    # Mismo IDOR que arriba, y aquí se LEE: el cliente_id sale del
    # token de sesión, no del path.
    grafo = await obtener_app()
    estado = await grafo.aget_state(config(cliente_id))
    if estado.next:      # el grafo sigue: no sirvas media respuesta
        return {"estado": "en_curso"}
    return {"estado": "listo",
            "respuesta": estado.values["messages"][-1].content}


# --- anadido del M17.2 (extraer_banco) ---
# Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro.
# se pega al final del servidor.py del 12.5: `logging` y `config`
# ya están importados allí, y `obtener_app` también.
import os
import time

import httpx
from fastapi import Response

BASE = os.environ["OPENAI_API_BASE"].removesuffix("/v1")
CLIENTE = httpx.AsyncClient(timeout=2.0)
_visto: tuple[float, bool] = (0.0, False)


async def _sano() -> bool:
    global _visto
    cuando, valor = _visto
    if time.monotonic() - cuando < 5.0:
        return valor
    try:
        # El checkpointer se prueba por donde lo usa el grafo, no
        # con un SELECT 1 por otra conexión: lo que se agota en
        # producción es el pool, y un SELECT 1 abre el suyo. Por
        # `obtener_app`, entonces, y con la lectura ASÍNCRONA: la
        # síncrona aquí lanza InvalidStateError (5.3).
        grafo = await obtener_app()
        await grafo.aget_state(config("sonda"))
        # /health/liveliness del 0.5 no llama a ningún proveedor.
        r = await CLIENTE.get(f"{BASE}/health/liveliness")
        valor = r.status_code == 200
    except Exception:
        # Sin esta línea el pod sale del balanceador y el log no
        # dice por qué: una sonda muda es una caída invisible.
        logging.exception("sonda de readiness en rojo")
        valor = False
    _visto = (time.monotonic(), valor)
    return valor


@api.get("/health/live")
def live():
    # Vivo = el proceso responde, y NADA más.
    return {"vivo": True}


@api.get("/health/ready")
async def ready(respuesta: Response):
    listo = await _sano()
    if not listo:
        respuesta.status_code = 503     # fuera del balanceador
    return {"listo": listo}


# --- costura PENDIENTE del M17.2 (extraer_banco) ---
# PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas.
# El script no la aplica en su sitio: eso es una decision. Ver COSTURAS.md.
# servidor.py --- lo que Kubernetes obliga a añadir al 12.5.
from contextlib import asynccontextmanager

# Por debajo de terminationGracePeriodSeconds (120) menos el
# preStop (10), y con margen: pasado el plazo es un SIGKILL.
CIERRE_S = 90


@asynccontextmanager
async def vida(api: FastAPI):
    yield                      # lo de abajo corre con el SIGTERM
    if VIVAS:
        await asyncio.wait(VIVAS, timeout=CIERRE_S)
    await CLIENTE.aclose()     # el cliente httpx de la sonda


api = FastAPI(lifespan=vida)   # sustituye al FastAPI() del 12.5
