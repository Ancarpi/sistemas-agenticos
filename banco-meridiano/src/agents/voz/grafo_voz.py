# grafo_voz.py --- el cerebro de la llamada. Dos herramientas y
# ninguna más: en voz, cada herramienta de más es un turno de más.
import os

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolCallLimitMiddleware, wrap_tool_call,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.config import get_stream_writer

from src.core.models import get_model      # la fábrica del 0.4

VOZ = """Eres el asistente telefónico de Banco Meridiano. Hablas
para ser OÍDO: frases de menos de veinte palabras, sin listas,
sin markdown y sin abreviaturas; los importes, en palabras. Nunca
pronuncias un IBAN entero: solo sus cuatro últimos dígitos, y los
repites y esperas un «sí» antes de bloquear nada. Si no has
entendido, pregunta: en voz, adivinar cuesta la llamada."""

PERMITIDAS = {"consultar_movimientos", "bloquear_tarjeta"}

# La regla del 13.5: p95 por encima de 1,2 s, frase antes de
# llamar. `bloquear_tarjeta` vuelve en 300 ms y no lleva.
ANTESALA = {
    "consultar_movimientos": "Miro sus últimos movimientos.",
}


@wrap_tool_call
async def hablar_antes_de_trabajar(peticion, siguiente):
    """El punto de inyección del 13.5. Las herramientas son
    objetos remotos del MCP: no hay cuerpo tuyo donde meter el
    emisor, y este hook del 4.2 es el único sitio que queda."""
    frase = ANTESALA.get(peticion.tool_call["name"])
    if frase:
        emitir = get_stream_writer()    # el mismo del 6.3
        emitir(frase + " ")
    return await siguiente(peticion)


async def construir_cerebro():
    """Las dos del Ejercicio 13.2, servidas por el MCP del 10.1."""
    cliente = MultiServerMCPClient({
        "core_bancario": {"url": os.environ["MCP_CORE_URL"],
                          "transport": "streamable_http"},
    })
    # Lista BLANCA, como las etiquetas del 6.3: el core expone
    # más herramientas y aquí solo entran dos.
    dos = [t for t in await cliente.get_tools()
           if t.name in PERMITIDAS]
    if len(dos) != len(PERMITIDAS):
        raise RuntimeError(f"el core expone {len(dos)} de 2")
    return create_agent(
        model=get_model("agente-rapido", temperature=0.3),
        tools=dos,
        system_prompt=VOZ,
        # El techo del 3.2 vive AQUÍ, no en la sesión de voz.
        middleware=[hablar_antes_de_trabajar,
                    ToolCallLimitMiddleware(run_limit=4,
                                            exit_behavior="end")],
    )
