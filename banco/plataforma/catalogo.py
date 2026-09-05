# catalogo.py --- el recorte, servido. Pega aquí el CATALOGO del
# 37.2 tal cual y de CINCO columnas: el `decidir` de allí hace
# `CATALOGO[n][3:]` y desempaqueta DOS. Y no importes `resolver` en
# el `grafo_conciliacion.py` del 5.3: allí es un NODO que el 5.3
# registra por `__name__` (6.3) y el import lo pisa.
import hashlib
import json
import logging
import pathlib
import time

from estado import ENTORNO            # el 32.2, fijado al importar

FICHAS = pathlib.Path("catalogo/aprobadas.json")   # control plane
TTL = 30            # segundos, y este número ES tu SLA de revocación
_visto = (float("-inf"), {})              # (instante, último bueno)


def firma(tool) -> str:
    """El 10.2 firmaba la descripción y no basta: un `dias: int` que
    pasa a `str | int` no toca el docstring y amplía lo que se pide."""
    s = tool.tool_call_schema             # las de MCP traen un dict
    s = s.model_json_schema() if hasattr(s, "model_json_schema") else s
    esquema = json.dumps(s, sort_keys=True)  # o el orden da otro hash
    return hashlib.sha256(
        (tool.description + esquema).encode()).hexdigest()[:16]


def aprobadas() -> dict:
    """nombre -> [firma, entornos], y sin último bueno se falla
    CERRADO: un agente sin herramientas no protesta, improvisa."""
    global _visto
    if time.monotonic() - _visto[0] < TTL:
        return _visto[1]
    try:
        nuevo = json.loads(FICHAS.read_text("utf-8"))
    except (OSError, ValueError):
        nuevo = {}     # un JSON a medio escribir tampoco revoca nada
        logging.warning("aprobadas.json ilegible: sirvo el último bueno")
    if nuevo:
        # Se asigna DESPUÉS de validar: cachear un {} legal haría
        # que el TTL entero sirviera vacío sin excepción.
        _visto = (time.monotonic(), nuevo)
    if not _visto[1]:
        raise RuntimeError("catálogo sin aprobaciones")
    return _visto[1]


def resolver(permitidas, entorno=ENTORNO):
    """El recorte: su `tools_allowed` cortado por lo que el catálogo
    sirve HOY y AQUÍ. `retired` no llega; `deprecated` sí."""
    fichas, sirven = aprobadas(), []
    for n in permitidas:
        tool, _, estado, _, _ = CATALOGO[n]    # KeyError a propósito
        aprobada, entornos = fichas.get(n, (None, []))
        if estado == "retired" or entorno not in entornos:
            logging.warning("%s: no servida en %s", n, entorno)
            continue
        if firma(tool) != aprobada:
            raise RuntimeError(f"{n}: definición sin aprobar")
        sirven.append(tool)
    return sirven


def sello_catalogo() -> str:
    """La terna del 33.4 MÁS la aprobación: sin esa segunda mitad,
    borrar una fila no purga el CACHE del 37.2."""
    f = aprobadas()
    return hashlib.sha256(repr(sorted(
        (n, x[1], x[2], f.get(n)) for n, x in CATALOGO.items()
    )).encode()).hexdigest()[:12]
