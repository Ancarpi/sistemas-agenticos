# fanout_nocturno.py --- triaje en paralelo de un lote de 20.
import operator
import time
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from src.core.models import get_model      # la fábrica del 0.4


class EstadoLote(TypedDict):
    referencias: list[str]                # entran: 20 incidencias
    # SIN este reducer, InvalidUpdateError: veinte nodos escriben
    # 'veredictos' en el MISMO superpaso y hay que decir cómo se
    # fusionan. Con operator.add, se concatenan.
    veredictos: Annotated[list[dict], operator.add]
    informe: str


TRIAJE = SystemMessage(
    "Clasifica la incidencia SEPA en una sola palabra: duplicado, "
    "fraude, comision o desconocido. Responde solo la palabra.")


def abanico(estado: EstadoLote) -> list[Send]:
    # El segundo argumento del Send es el estado ENTERO con el que
    # arranca la rama, no una actualización parcial del padre.
    return [Send("triar_una", {"referencia": r})
            for r in estado["referencias"]]


def triar_una(estado: dict) -> dict:
    modelo = get_model("agente-rapido", temperature=0)
    r = modelo.invoke([TRIAJE, HumanMessage(estado["referencia"])])
    # Lista de un elemento: es lo que el reducer concatena. Y la
    # referencia va DENTRO, nunca implícita en la posición.
    return {"veredictos": [{"referencia": estado["referencia"],
                            "categoria": r.text.strip().lower()}]}


def reducir(estado: EstadoLote) -> dict:
    conteo: dict[str, int] = {}
    for v in estado["veredictos"]:
        conteo[v["categoria"]] = conteo.get(v["categoria"], 0) + 1
    return {"informe": f"{len(estado['veredictos'])} triadas: {conteo}"}


g = StateGraph(EstadoLote)
g.add_node("triar_una", triar_una)
g.add_node("reducir", reducir)
g.add_conditional_edges(START, abanico, ["triar_una"])  # cuelga de START
g.add_edge("triar_una", "reducir")    # las 20 ramas confluyen aquí
g.add_edge("reducir", END)
# Sin checkpointer para que el ejemplo quepa; el batch del M11 va
# con PostgresSaver y un thread_id por lote, y la trampa 3 dice por qué.
app = g.compile()

if __name__ == "__main__":
    t0 = time.perf_counter()
    salida = app.invoke(
        {"referencias": [f"REF-{n}" for n in range(4451, 4471)],
         "veredictos": []},
        # Sin este techo salen 20 peticiones a la vez y el gateway
        # devuelve 429: el rpm: 400 del 0.5 son 6,6 por segundo.
        config={"max_concurrency": 5},
    )
    print(salida["informe"])
    print(f"{time.perf_counter() - t0:.1f} s")
