# src/evals/trayectoria.py --- los casos de los dos planos que el
# 15.7 no cubre. Aquí se PRODUCE la fracción de aciertos; quien la
# compara con un umbral y firma el veredicto es `medir` (15.7).
import asyncio
import json
import uuid
from dataclasses import dataclass

from pydantic import BaseModel

from evals.medidas import cargar             # el conjunto del 15.7
from grafo_conciliacion import obtener_app   # la fábrica del 5.3
from identidad import hilo                   # el thread_id del 18.3
from src.core.models import get_model        # la fábrica del 0.4


async def recorrer(app, entrada: dict, cfg: dict) -> list[str]:
    """Nodos y herramientas, en orden y con repeticiones."""
    t: list[str] = []
    async for paso in app.astream(entrada, cfg,
                                  stream_mode="updates"):
        for nodo, delta in paso.items():
            # Solo `updates` da los nodos, y el `__interrupt__` es
            # uno más; ese, además, trae una tupla y no un delta.
            t.append(nodo)
            d = delta if isinstance(delta, dict) else {}
            t += [c["name"] for m in d.get("messages", [])
                  for c in getattr(m, "tool_calls", ())]
    return t


def fallos(t: list[str], inv: dict) -> list[str]:
    """Solo lo que el procedimiento exige, y la prohibida siempre."""
    m = [f"prohibida {h}" for h in inv.get("prohibidas", ()) if h in t]
    m += [f"falta {h}" for h in inv.get("requeridas", ()) if h not in t]
    for antes, despues in inv.get("orden", ()):
        # Solo si el segundo OCURRIÓ: exigirlo cuando el caso ni
        # llegó ahí cuenta dos veces el mismo fallo.
        if despues in t and antes not in t[:t.index(despues)]:
            m.append(f"orden: {despues} sin {antes} delante")
    return m


async def _correr(casos: list[dict], uno) -> float:
    """Un solo `asyncio.run` por pasada, y de ahí el async: uno por
    caso abre un bucle nuevo y el grafo del 5.3 quedó en el otro."""
    app, sello, ok = await obtener_app(), uuid.uuid4().hex[:8], 0
    for c in casos:
        # El hilo lleva el sello de la PASADA: `medir` repite la
        # semilla, y un thread_id estable releería el checkpoint.
        cfg = {"configurable": {"thread_id": hilo(
            "conciliacion", f"{c['hilo']}#{sello}")}}
        try:
            f = await uno(app, c, cfg)
        except Exception as e:
            # Cuenta como fallo: sin trayectoria no hay prohibida.
            f = [str(e)[:120]]
        ok += not f
        if f:
            print(f"{c['hilo']}: {', '.join(f)}")
    return ok / len(casos)


async def _un_caso(app, c: dict, cfg: dict) -> list[str]:
    entrada = {"referencia": c["referencia"],
               "messages": [("user", c["pregunta"])]}
    return fallos(await recorrer(app, entrada, cfg), c["invariantes"])


def trayectorias(n: int, corpus: str, semilla: int) -> float:
    """Firma de medida del 15.7, para entrar en su `PUERTAS`."""
    return asyncio.run(_correr(
        cargar("trayectorias", "v1", n, semilla), _un_caso))
