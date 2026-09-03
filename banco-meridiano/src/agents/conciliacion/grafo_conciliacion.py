# grafo_conciliacion.py --- ANDAMIO, no codigo entregado por el libro.
#
# El libro nunca publica este fichero entero: lo pide como Ejercicio 5.1 y
# despues lo da por existente (`from grafo_conciliacion import app` en el
# 6.3 y en el 12.5). Aqui van las dos piezas que si estan escritas --- el
# estado y el grafo del 5.1, y el nodo `investigar` del 6.3 --- y falta lo
# que el ejercicio te pide teclear:
#
#   TODO Ejercicio 5.1: nodo_triage, nodo_resolver y nodo_revision, la
#   funcion ruta_por_urgencia y consultar_core(referencia). Compila con
#   PostgresSaver (5.2) y un thread_id por incidencia.
#
# Sin ellos este modulo NO importa: `g.add_node` recibe nombres que no
# existen. Es un andamio honesto, no una pieza que corre.


# --- anadido del M5.1 (extraer_meridiano) ---
# El estado y el grafo del 5.1: EstadoBackoffice, nodos y aristas.
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class EstadoBackoffice(TypedDict):
    messages: Annotated[list, add_messages]   # reducer: acumula
    referencia: str
    categoria: str | None                     # sin reducer: se sobrescribe
    resuelto: bool

g = StateGraph(EstadoBackoffice)
g.add_node("triage", nodo_triage)
g.add_node("resolver", nodo_resolver)
g.add_node("revision_humana", nodo_revision)
g.add_edge(START, "triage")
g.add_conditional_edges("triage", ruta_por_urgencia,
                        {"auto": "resolver", "humano": "revision_humana"})
g.add_edge("resolver", END)
g.add_edge("revision_humana", END)   # sin ella la rama humana no cierra
app = g.compile()


# --- anadido del M6.3 (extraer_meridiano) ---
# El nodo investigar del 6.3, que el propio libro coloca en este fichero.
# Este nodo es el `investigar` de tu `grafo_conciliacion.py`, el
# del Ejercicio 5.1; si no lo registras, `stream_mode="custom"`
# no imprime absolutamente nada.
from langgraph.config import get_stream_writer


def nodo_investigar(estado: dict) -> dict:
    """Sin las dos líneas de `emitir`, los tres segundos que tarda
    el core bancario son un spinner mudo."""
    emitir = get_stream_writer()
    emitir({"fase": "core", "pct": 10})
    movs = consultar_core(estado["referencia"])   # 3 s de espera
    emitir({"fase": "core", "pct": 100, "n": len(movs)})
    return {"movimientos": movs}
