# cliente_core.py --- el agente del 4.3, con las tools del core.
import asyncio
import hashlib
import json
import logging
import pathlib

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.core.models import get_model         # la fábrica del 0.4

SERVIDORES = {
    "core": {"url": "https://core-mcp.meridiano.internal/mcp",
             "transport": "streamable_http"},  # aquí SÍ con guion bajo
    "crm": {"url": "https://crm-mcp.meridiano.internal/mcp",
            "transport": "streamable_http"},
}
# La allow-list, con el nombre YA prefijado y el sha256 de la
# descripción aprobada en revisión: la «fijación de versión» del
# 10.1. Si cambia una descripción aprobada, el agente no arranca.
# El fichero es {"core_historial_cuenta": "<sha256 de la
# descripción>", ...}; la primera versión la escribes pegando la
# salida de este mismo bucle: imprime t.name y firma, y revísala.
APROBADAS: dict[str, str] = json.loads(
    pathlib.Path("docs/mcp-aprobadas.json").read_text("utf-8"))


async def construir_agente():
    cli = MultiServerMCPClient(SERVIDORES, tool_name_prefix=True)
    montadas = []
    for t in await cli.get_tools():     # prefijo = nombre del servidor
        firma = hashlib.sha256(t.description.encode()).hexdigest()
        if t.name not in APROBADAS:
            logging.warning("MCP ofrece y no monto: %s", t.name)
        elif firma != APROBADAS[t.name]:
            raise RuntimeError(f"descripción cambiada: {t.name}")
        else:
            montadas.append(t)
    if faltan := set(APROBADAS) - {t.name for t in montadas}:
        raise RuntimeError(f"no las sirve nadie: {faltan}")
    return create_agent(model=get_model("agente-listo"), tools=montadas)


agente = asyncio.run(construir_agente())
