# grafo_conciliacion.py --- el back-office del 4.3, ahora grafo.
# Mismo core del 3.3 y mismas herramientas del 4.1: lo único que
# cambia de manos es QUIÉN decide el orden de los pasos.
import asyncio
import json
import os
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, Field

import nano_agent as core                    # el 3.3, intacto
from herramientas import (devolver_transferencia, escalar_a_humano,
                          marcar_resuelta)   # decoradas, del 4.1
from src.core.models import get_model        # la fábrica del 0.4


class EstadoBackoffice(TypedDict):
    """El contrato con el 6.3 y el 12.5. `referencia` la pone quien
    abre el hilo; el resto lo escriben los nodos, y por eso los
    NODOS lo leen con `.get()` y no con corchetes."""
    messages: Annotated[list, add_messages]   # reducer: acumula
    referencia: str
    categoria: str | None                     # sin reducer: pisa
    urgencia: int | None
    movimientos: list                         # lo que emite el 6.3
    resuelto: bool


ESCRITURA = [marcar_resuelta, escalar_a_humano,
             devolver_transferencia]      # la 5.a sale del Ej. 3.1
# El MISMO despacho que usa el ToolNode de abajo. Si en cambio
# `revision_humana` ejecutase por el `DESPACHO` del 3.3, la
# devolución no existiría allí --- son cuatro herramientas --- y
# el aprobador de N2 vería un NO_TOOL donde espera dinero movido.
POR_NOMBRE = {t.name: t for t in ESCRITURA}


class Triaje(BaseModel):
    categoria: Literal["duplicado", "no_recibida", "fraude", "otra"]
    urgencia: int = Field(ge=1, le=5, description="5 = dinero "
                          "fuera y cliente esperando")


def triage(estado: EstadoBackoffice) -> dict:
    """Salida estructurada, no prosa (2.3): de aquí sale la rama,
    y una rama no se decide leyendo un párrafo."""
    modelo = get_model("agente-rapido", temperature=0)
    t = modelo.with_structured_output(Triaje).invoke(
        estado["messages"])
    return {"categoria": t.categoria, "urgencia": t.urgencia}


def consultar_core(referencia: str) -> list[dict]:
    """El `consultar_core` que el 6.3 nombra: las dos lecturas que
    en la traza del 3.3 el modelo pidió siempre en el mismo orden
    --- un paso que no se ramifica no necesita un modelo que lo
    decida ---, y con ellas se van dos de aquellas cuatro llamadas
    y 1.490 tokens medidos. Devuelve la LISTA de movimientos: es
    lo que el 6.3 mide con len() y lo que viaja por el canal
    `movimientos`. Si devuelves el dict de las dos lecturas, el
    6.3 no revienta aquí: revienta en `notificar`."""
    t = core.buscar_transferencia(referencia)
    if "error" in t:
        return []
    return core.historial_cuenta(t["iban"])["movimientos"]


def investigar(estado: EstadoBackoffice) -> dict:
    """Aquí dentro van las dos líneas de `get_stream_writer()` del
    6.3: es el único nodo lento que no es un LLM, y sin ellas los
    tres segundos del core son un spinner mudo."""
    return {"movimientos": consultar_core(estado["referencia"])}


def resolver(estado: EstadoBackoffice) -> dict:
    """Solo herramientas de ESCRITURA: leer ya lo hizo el grafo.
    El bucle del 3.3 no ha desaparecido --- son este nodo, el de
    herramientas y la arista de vuelta ---, pero le has quitado la
    mitad de las vueltas y toda la decisión de orden."""
    modelo = get_model("agente-listo").bind_tools(ESCRITURA)
    hechos = json.dumps(estado.get("movimientos", []),
                        ensure_ascii=False)
    return {"messages": [modelo.invoke(
        [SystemMessage(core.SISTEMA),
         SystemMessage(f"Movimientos del core: {hechos}"),
         *estado["messages"]])]}


def revision_humana(estado: EstadoBackoffice) -> dict:
    """El grafo se PARA aquí y el estado se queda en Postgres: la
    respuesta puede llegar dos días después (6.1), y las dos
    claves de la decisión son las que el 6.1 imprime."""
    llamadas = estado["messages"][-1].tool_calls
    d = interrupt({"referencia": estado["referencia"],
                   "urgencia": estado.get("urgencia"),
                   "acciones": [c["name"] for c in llamadas],
                   "movimientos": estado.get("movimientos", [])})
    # Cada tool_call pendiente necesita SU ToolMessage, aprobado o
    # rechazado. El que dejes sin contestar no revienta aquí:
    # revienta la llamada de `notificar`, con un 400 del proveedor
    # que habla de un `tool_call_id` que tú no has escrito.
    salidas = [ToolMessage(
        json.dumps(POR_NOMBRE[c["name"]].invoke(c["args"]),
                   ensure_ascii=False) if d["aprobado"]
        else f"RECHAZADO por N2: {d['motivo_rechazo']}",
        tool_call_id=c["id"]) for c in llamadas]
    return {"messages": salidas, "resuelto": d["aprobado"]}


REDACTA = """Redacta la respuesta al cliente con lo que digan los
mensajes anteriores y nada más. Si una acción salió RECHAZADA por
N2, dilo sin excusarte y di que la lleva ya una persona."""


def notificar(estado: EstadoBackoffice) -> dict:
    """El único nodo cuyos tokens ve el cliente (6.3), y de ahí el
    alias: el 0.5 reserva `agente-equilibrado` para lo que lee una
    persona."""
    modelo = get_model("agente-equilibrado")
    return {"messages": [modelo.invoke(
        [SystemMessage(REDACTA), *estado["messages"]])]}


def ruta_triaje(estado: EstadoBackoffice) -> str:
    """Por categoría: lo que no habla de una transferencia
    concreta no tiene nada que buscar en el core. Las funciones de
    ARISTA sí leen con corchetes: `triage` corre siempre antes."""
    if estado["categoria"] == "otra":
        return "notificar"
    return "investigar"


def ruta_resolver(estado: EstadoBackoffice) -> str:
    ultimo = estado["messages"][-1]
    if not ultimo.tool_calls:             # parada natural (3.3)
        return "notificar"
    # Por urgencia, y el umbral es de negocio, no del modelo: la
    # MISMA acción se ejecuta sola en un caso de urgencia 3 y
    # espera a N2 en uno de urgencia 4.
    if estado["urgencia"] >= 4 or any(
            c["name"] == "devolver_transferencia"
            for c in ultimo.tool_calls):
        return "revision_humana"
    return "herramientas"


g = StateGraph(EstadoBackoffice)
for nodo in (triage, investigar, resolver, revision_humana,
             notificar):
    g.add_node(nodo.__name__, nodo)     # los cinco nombres del 6.3
g.add_node("herramientas", ToolNode(ESCRITURA))
g.add_edge(START, "triage")
g.add_conditional_edges("triage", ruta_triaje,
                        ["investigar", "notificar"])
g.add_edge("investigar", "resolver")
g.add_conditional_edges("resolver", ruta_resolver,
                        ["herramientas", "revision_humana",
                         "notificar"])
g.add_edge("herramientas", "resolver")     # el ciclo del 3.3
g.add_edge("revision_humana", "notificar")
g.add_edge("notificar", END)          # sin esto no cierra la rama

# El 5.2 abría el checkpointer con `with` y al salir del bloque
# cerraba el pool: vale para un script, no para el `servidor.py`
# del 12.5, que lo usa durante meses. Pero un `app` compilado aquí
# mismo tampoco vale, y esta es la trampa que cuesta la tarde:
# `PostgresSaver` no tiene métodos async --- hereda los de la
# clase base, que lanzan NotImplementedError ---, así que el
# `astream` del canal del 6.3 muere en el primer superpaso; y
# `AsyncPostgresSaver` no se puede construir al importar, porque
# su __init__ pide un loop corriendo. Lo que se exporta, entonces,
# no es un grafo: es una FÁBRICA, y el grafo se compila dentro del
# loop que lo va a usar.
_APP = None
_CANDADO = asyncio.Lock()


async def obtener_app():
    """Una vez por proceso. Y el `autocommit` no es adorno: sin
    él, el `setup()` no falla en silencio --- revienta en el acto
    con `ActiveSqlTransaction --- CREATE INDEX CONCURRENTLY cannot
    run inside a transaction block`, porque tres de las
    migraciones del checkpointer crean sus índices fuera de
    transacción."""
    global _APP
    async with _CANDADO:              # dos peticiones, un pool
        if _APP is None:
            pool = AsyncConnectionPool(
                os.environ["DATABASE_URL"], open=False,
                max_size=20, kwargs={"autocommit": True})
            await pool.open()
            cp = AsyncPostgresSaver(pool)
            await cp.setup()       # idempotente; en M17, migración
            _APP = g.compile(checkpointer=cp)
    return _APP


if __name__ == "__main__":
    HILO = {"configurable":
            {"thread_id": "conciliacion|incidencia:REF-4471"}}

    async def demo():
        app = await obtener_app()
        r = await app.ainvoke(
            {"referencia": "REF-4471",
             "messages": [("human", "Me han cobrado dos veces la "
                                    "REF-4471")]}, HILO)
        if r.get("__interrupt__"):    # se paró en revision_humana
            print(r["__interrupt__"][0].value)
            r = await app.ainvoke(
                Command(resume={"aprobado": True,
                                "motivo_rechazo": ""}), HILO)
        print(r["messages"][-1].content)
        print(app.get_graph().draw_mermaid())   # punto 4 del Ej. 5.1

    asyncio.run(demo())


# --- anadido del M6.3 (extraer_banco) ---
# El nodo investigar del 6.3, que el propio libro coloca en este fichero.
# Este nodo es el `investigar` del 5.3 con las dos líneas que
# allí faltan; si no las registras, `stream_mode="custom"` no
# imprime absolutamente nada. Y se llama `investigar` y no
# `nodo_investigar`: el 5.3 registra los nodos por `__name__`.
from langgraph.config import get_stream_writer


def investigar(estado: dict) -> dict:
    """Sin las dos líneas de `emitir`, los tres segundos que tarda
    el core bancario son un spinner mudo."""
    emitir = get_stream_writer()
    emitir({"fase": "core", "pct": 10})
    movs = consultar_core(estado["referencia"])   # 3 s de espera
    emitir({"fase": "core", "pct": 100, "n": len(movs)})
    return {"movimientos": movs}
