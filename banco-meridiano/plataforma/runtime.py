# plataforma/runtime.py --- nadie importa un grafo: se pide por id.
import uuid

from langchain.agents import create_agent
from plataforma import catalogo, hitl, identidad, politica, registro, trazas
from plataforma.estado import ENTORNO, SAVER, STORE
from src.core.models import get_model      # la fábrica del 0.4

GRAFOS = {}


def compilar(pk, sello, propio=None):
    """La clave lleva el sello del catálogo --- hash de las ternas
    (nombre, `version`, `status`) del 33.4: sin él, marcar una tool
    `retired` no revoca nada. `propio`: el grafo del paquete (9.2)."""
    clave = (pk.id, pk.version, sello)
    if clave not in GRAFOS:
        GRAFOS[clave] = propio or create_agent(
            model=get_model(pk.models["supervisor"]),
            tools=catalogo.resolver(pk.tools_allowed),   # 33.3
            middleware=[guardia], checkpointer=SAVER, store=STORE)
    return GRAFOS[clave]


async def ejecutar(agente_id, sujeto, texto, proposito, humano):
    """El hilo no se inventa aquí: es el `hilo(grafo, sujeto)` del
    18.3 --- con el agente delante, porque el checkpointer indexa
    por thread_id ---, y `sujeto` llega con su clase: `cliente:C-99`."""
    pk, sello, propio = registro.cargar(agente_id)      # el 32.3
    ctx = {"sujeto": sujeto, "humano": humano, "run": uuid.uuid4().hex,
           "proposito": proposito, "entorno": ENTORNO,
           "agente": {"id": pk.id, "version": pk.version},
           "hilo": identidad.hilo(pk.id, sujeto),          # 18.3
           "ns": (pk.tenant, proposito, sujeto)}   # jamás el agente
    cfg = {"configurable": {"thread_id": ctx["hilo"]},
           "metadata": trazas.atributos(pk, ctx["run"], sujeto)}  # 36.1
    return await compilar(pk, sello, propio).ainvoke(
        {"messages": [("user", texto)]}, cfg, context=ctx)
# La política y el HITL, en el mismo `wrap_tool_call` del 4.2 que
# ya usaste en el 13.4: una decisión por llamada, para los cuatro.
@wrap_tool_call
def guardia(peticion, siguiente):
    ctx, llamada = peticion.runtime.context, peticion.tool_call
    # El dict del 35.2 sin tocar (`politica` es su policy engine).
    # La tool va por su nombre: `peticion.tool` es None si retirada.
    decision = politica.authorize({
        "subject": {"user_id": ctx["sujeto"]}, "agent": ctx["agente"],
        "tool": {"id": llamada["name"]},
        "context": {"purpose": ctx["proposito"], "env": ctx["entorno"]}})
    if decision == "require_human":
        # Se reanuda con el hilo, nunca con el run. Y quien PROPONE
        # es el humano que delegó, jamás el agente (regla del 35.4).
        hitl.encolar(hilo=ctx["hilo"], run=ctx["run"],
                     agente=ctx["agente"], propone=ctx["humano"],
                     propuesta=llamada["args"])
        interrupt({"run": ctx["run"]})
    elif decision != "allow":      # dry-run y step-up: aún no están
        return ToolMessage(f"política: {decision}",
                           tool_call_id=llamada["id"])
    return siguiente(peticion)
