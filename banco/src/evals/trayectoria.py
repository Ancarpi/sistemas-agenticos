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


# --- anadido del M25.7 (extraer_banco) ---
# Anadido del M25.7.
# src/evals/trayectoria.py (sigue) --- el usuario simulado del
# 25.6. La conversación entera la juzga el `fallos` de arriba.
USUARIO = "agente-rapido-backup"   # el otro lado, de otro proveedor


@dataclass(frozen=True)
class Usuario:
    perfil: str      # cómo escribe, de qué humor y qué no hace
    objetivo: str    # qué considera ÉL haber terminado
    oculto: dict     # lo que solo suelta si se lo preguntan
    paciencia: int = 6      # mensajes suyos antes de irse


class Replica(BaseModel):
    """texto: lo que escribe, una o dos frases. entregado: claves
    de `oculto` que acaba de dar. conseguido: si ya tiene lo suyo."""
    texto: str
    entregado: list[str] = []
    conseguido: bool


GUION = """Eres un cliente del banco escribiendo por el chat. No
eres un asistente y no ayudas a nadie: tienes un problema tuyo.
Perfil: {perfil}. Objetivo: {objetivo}.
Solo sabes esto, y cada dato lo sueltas ÚNICAMENTE si te lo piden
en el último mensaje: {oculto}
Te quedan {quedan} mensajes de paciencia; al acabarse, te vas. No
resumas la conversación ni des las gracias por el trabajo.
Conversación:
{historia}"""


async def conversar(app, u: Usuario, ref: str, cfg: dict) -> dict:
    """Termina cuando él consigue lo suyo o cuando se le acaba la
    paciencia, y ninguna de las dos la decide el agente."""
    modelo = get_model(USUARIO).with_structured_output(Replica)
    historia, dados, repetidos, t = [], [], [], []
    for turno in range(1, u.paciencia + 1):
        # El perfil viaja en TODOS los turnos, no solo en el primero.
        r = modelo.invoke(GUION.format(
            perfil=u.perfil, objetivo=u.objetivo,
            quedan=u.paciencia - turno + 1,
            oculto=json.dumps(u.oculto, ensure_ascii=False),
            historia="\n".join(historia) or "(nada aún)"))
        if r.conseguido:
            break        # se va contento, y este mensaje no cuenta
        # Si entrega dos veces la misma clave, se la han pedido dos.
        repetidos += [k for k in r.entregado if k in dados]
        dados += r.entregado
        historia.append(f"Cliente: {r.texto}")
        # La traza se CONCATENA: cada `astream` emite solo lo suyo.
        entrada = {"referencia": ref, "messages": [("user", r.texto)]}
        t += await recorrer(app, entrada, cfg)
        m = (await app.aget_state(cfg)).values["messages"][-1]
        historia.append(f"Asistente: {m.content}")
    return {"turnos": turno, "conseguido": r.conseguido, "traza": t,
            "repetidos": repetidos,
            "escalado": "escalar_a_humano" in t}


async def _una_charla(app, c: dict, cfg: dict) -> list[str]:
    r = await conversar(app, Usuario(**c["usuario"]), c["referencia"],
                        cfg)
    # El `conseguido` esperado es FALSO en el perfil que insiste.
    m = fallos(r["traza"], c["invariantes"])
    m += [f"repetido {k}" for k in r["repetidos"]]
    m += [k for k in ("conseguido", "escalado") if r[k] != c[k]]
    return m + (["turnos"] if r["turnos"] > c["turnos"] else [])


def conversaciones(n: int, corpus: str, semilla: int) -> float:
    """Dos modelos por caso: puerta antes del canary (25.6)."""
    return asyncio.run(_correr(
        cargar("conversaciones", "v1", n, semilla), _una_charla))
