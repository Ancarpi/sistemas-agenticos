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

# Las veinte del lote, con el texto que el modelo clasifica. La
# semilla vive junto al fichero que la usa, igual que las tres
# transferencias del 3.3; en el M11 estas veinte salen de una
# consulta a `banco.incidencias` y el resto no cambia.
INCIDENCIAS = {
    "REF-4451": "Dos cargos iguales de 1.284,50 EUR el mismo día.",
    "REF-4452": "Me han cobrado 12,00 EUR de gastos sin avisarme.",
    "REF-4453": "El recibo del gimnasio lo han pasado dos veces.",
    "REF-4454": "Pago de 890,00 EUR en Ucrania que no autoricé.",
    "REF-4455": "Mismo importe y beneficiario, un minuto de hueco.",
    "REF-4456": "Cargo de mantenimiento de cuenta que no esperaba.",
    "REF-4457": "Pagué la luz una vez y veo dos apuntes idénticos.",
    "REF-4458": "Repetido: 249,00 EUR a la misma cuenta, dos veces.",
    "REF-4459": "Gastos por transferencia inmediata, 1,50 EUR.",
    "REF-4460": "La renta de mi casero salió duplicada en agosto.",
    "REF-4461": "Compra con mi tarjeta a las 04:12, no soy yo.",
    "REF-4462": "Dos transferencias gemelas de 90,00 EUR seguidas.",
    "REF-4463": "Comisión de 3,00 EUR por sacar en otro cajero.",
    "REF-4464": "Me consta un solo envío y el extracto trae dos.",
    "REF-4465": "Cargo doble del seguro, 412,30 EUR cada apunte.",
    "REF-4466": "Me aplican gastos de descubierto de 18,00 EUR.",
    "REF-4467": "Cinco cargos seguidos de una web que no conozco.",
    "REF-4468": "Envié una transferencia y el banco emitió dos.",
    "REF-4469": "Cobro de 30,00 EUR por reclamación de recibo.",
    "REF-4470": "Duplicidad de 75,00 EUR, quince segundos de hueco.",
}


def abanico(estado: EstadoLote) -> list[Send]:
    # El segundo argumento del Send es el estado ENTERO con el que
    # arranca la rama, no una actualización parcial del padre.
    return [Send("triar_una", {"referencia": r,
                               "texto": INCIDENCIAS[r]})
            for r in estado["referencias"]]


def triar_una(estado: dict) -> dict:
    modelo = get_model("agente-rapido", temperature=0)
    r = modelo.invoke([TRIAJE, HumanMessage(estado["texto"])])
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
        {"referencias": list(INCIDENCIAS),
         "veredictos": []},
        # El techo mantiene la ráfaga por debajo de la cuota
        # que ata, el `rpm_limit: 60` de la clave virtual del
        # 0.5. Estas veinte gastan 20 de esos 60 y ninguna ve
        # un 429; las cinco mil del lote grande cruzan la
        # cuota dentro del primer minuto, y ahí sí llega.
        config={"max_concurrency": 5},
    )
    print(salida["informe"])
    print(f"{time.perf_counter() - t0:.1f} s")
