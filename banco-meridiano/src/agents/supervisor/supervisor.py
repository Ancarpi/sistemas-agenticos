# supervisor.py --- el multi-agente de Meridiano. El contrato de
# traspaso es el TypedDict de abajo: lo que no este ahi, no cruza.
import json
from datetime import datetime, timedelta
from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ToolMessage,
)
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from src.core.models import get_model        # la fábrica del 0.4
from src.core.banco import TRANSFERENCIAS, eur   # los dicts del 3.3


class Hecho(TypedDict):
    autor: str      # qué trabajador lo estableció
    dato: str       # una frase, con la herramienta citada dentro


class EstadoMeridiano(TypedDict):
    """EL CONTRATO DE TRASPASO. No hay campo `messages`: la
    conversación interna de un trabajador no cruza un handoff."""
    cliente: str                # un identificador, nunca el IBAN
    referencia: str
    consulta: str
    # add: los hechos se ACUMULAN. Sin reducer, el segundo
    # trabajador pisa lo que averiguó el primero.
    hechos: Annotated[list[Hecho], add]
    encargo: str                # qué pide el supervisor AHORA
    devuelto_por: str | None    # quién no pudo, y qué le faltaba
    saltos: int                 # el techo del 3.2, entre agentes
    respuesta: str


def briefing(estado: EstadoMeridiano) -> str:
    """La superficie de contacto entera. Si un trabajador sabe
    algo, es porque salió por aquí: esa es la definición."""
    lineas = [f"Cliente {estado['cliente']}, caso "
              f"{estado['referencia']}.",
              f"El cliente dice: {estado['consulta']}",
              f"Tu encargo: {estado['encargo']}"]
    for h in estado["hechos"]:
        lineas.append(f"Ya establecido por {h['autor']}: {h['dato']}")
    if estado["devuelto_por"]:
        lineas.append(f"Devuelto antes por {estado['devuelto_por']}")
    return "\n".join(lineas)
SUPERVISOR = """Eres el supervisor del back-office de Meridiano.
Tu única salida es decidir quién sigue: no resuelves tú y no
inventas hechos que no te haya dado un trabajador.
- facturacion: comisiones, recibos, duplicados, devoluciones.
- fraude: cargos no reconocidos, bloqueos, disputas.
- responder: ya hay hechos suficientes para contestar al cliente.
Si un trabajador te devolvió el caso, NO se lo reenvíes con el
mismo encargo: reformúlalo con lo que le faltaba, o ve a
responder y pídeselo al cliente."""


class Ruta(BaseModel):
    destino: Literal["facturacion", "fraude", "responder"]
    encargo: str = Field(description="Una frase imperativa: qué "
                                     "tiene que averiguar o hacer")
    motivo: str = Field(description="Por qué. Va a la traza")


def supervisor(estado: EstadoMeridiano) -> Command[
        Literal["facturacion", "fraude", "responder"]]:
    if estado["saltos"] >= 6:
        return Command(
            goto="responder",
            update={"devuelto_por": "supervisor: techo de saltos"})
    router = get_model("agente-listo").with_structured_output(Ruta)
    ruta = router.invoke([SystemMessage(SUPERVISOR),
                          HumanMessage(briefing(estado))])
    print(json.dumps({"salto": estado["saltos"] + 1,
                      "a": ruta.destino, "motivo": ruta.motivo},
                     ensure_ascii=False))
    return Command(
        goto=ruta.destino,
        update={"encargo": ruta.encargo,
                "saltos": estado["saltos"] + 1,
                # se limpia al repartir, NO al responder: quien
                # redacta tiene que saber qué quedó abierto.
                "devuelto_por": estado["devuelto_por"]
                if ruta.destino == "responder" else None},
    )
CLIENTES = {"C-99": "ES9121000418450200051332"}
DISPUTAS: dict = {}


def enmascarar(iban: str) -> str:
    """Decisión 6 del 3.2: enmascarar es código, no una consigna."""
    return f"{iban[:4]}****{iban[-4:]}"


@tool
def buscar_transferencia(referencia: str) -> dict:
    """Datos de una transferencia SEPA. Formato REF-NNNN."""
    t = TRANSFERENCIAS.get(referencia)
    if t is None:
        return {"error": "NOT_FOUND", "referencia": referencia}
    return {"importe": eur(t["importe_cent"]), "fecha": t["fecha"],
            "beneficiario": enmascarar(t["beneficiario"]),
            "concepto": t["concepto"]}


@tool
def buscar_duplicados(referencia: str) -> dict:
    """Transferencias con el mismo importe y beneficiario."""
    t = TRANSFERENCIAS.get(referencia)
    if t is None:
        # Sin esta guarda, una referencia mal tecleada devolvería
        # «no hay gemelas» y el agente lo afirmaría tan tranquilo.
        return {"error": "NOT_FOUND", "referencia": referencia}
    clave = (t["importe_cent"], t["beneficiario"])
    gemelas = [{"referencia": r, "fecha": o["fecha"]}
               for r, o in TRANSFERENCIAS.items()
               if r != referencia
               and (o["importe_cent"], o["beneficiario"]) == clave]
    return {"referencia": referencia, "gemelas": gemelas}


@tool
def historial_cliente(cliente: str, dias: int = 7) -> dict:
    """Movimientos recientes por identificador de cliente. El IBAN
    se resuelve aquí dentro y no sale en la respuesta."""
    if not 1 <= dias <= 90:
        # El 3.3 otra vez: el esquema es la primera defensa, no la
        # única. Un handoff no exime de volver a comprobar.
        return {"error": "INVALID_ARGUMENT", "mensaje": "dias 1-90"}
    iban = CLIENTES.get(cliente)
    if iban is None:
        return {"error": "NOT_FOUND", "cliente": cliente}
    desde = datetime.now() - timedelta(days=dias)
    return {"cliente": cliente, "dias": dias, "movimientos": [
        {"referencia": r, "importe": eur(t["importe_cent"]),
         "concepto": t["concepto"], "fecha": t["fecha"],
         "recurrente": t["concepto"].lower().startswith("cuota")}
        for r, t in TRANSFERENCIAS.items() if t["iban"] == iban
        and datetime.fromisoformat(t["fecha"]) >= desde]}


@tool
def abrir_disputa(referencia: str, motivo: str,
                  confirmado_por_cliente: bool) -> dict:
    """Abre una disputa formal por un cargo. Exige que el cliente
    haya confirmado por escrito que no lo reconoce."""
    if not confirmado_por_cliente:
        return {"error": "NEEDS_CONFIRMATION",
                "mensaje": "Sin confirmación escrita del cliente no "
                           "se puede abrir. Pídesela y vuelve."}
    DISPUTAS[referencia] = {"motivo": motivo, "estado": "abierta"}
    return {"ok": True, "referencia": referencia, "sla_dias": 15}
class Informe(BaseModel):
    """Lo único que un trabajador devuelve al estado compartido."""
    hechos: list[str] = Field(description="Un hecho por frase, "
                              "citando la herramienta que lo dio")
    resuelto: bool = Field(description="False si no pudiste")
    me_falta: str | None = Field(
        default=None, description="Si resuelto es False: qué te "
                                  "falta exactamente para cerrarlo")


CIERRE = ("Cierra tu parte: qué hechos has establecido y si has "
          "cumplido el encargo. No redactes nada para el cliente.")


def trabajador(nombre: str, sistema: str, kit: list):
    despacho = {h.name: h for h in kit}

    def nodo(
        estado: EstadoMeridiano,
    ) -> Command[Literal["supervisor"]]:
        modelo = get_model("agente-rapido", temperature=0)
        modelo = modelo.bind_tools(kit)
        # Su historial NACE aquí y MUERE aquí. Como no vive en el
        # estado, no puede cruzar el handoff ni por descuido.
        local = [SystemMessage(sistema),
                 HumanMessage(briefing(estado))]
        entrada = 0
        for _ in range(4):
            r: AIMessage = modelo.invoke(local)
            entrada += (r.usage_metadata or {}).get("input_tokens", 0)
            local.append(r)
            if not r.tool_calls:
                break
            for c in r.tool_calls:
                # Decisión 2 del 3.2: un nombre alucinado es un
                # error esperable, no una excepción que tumba el nodo.
                h = despacho.get(c["name"])
                salida = (h.invoke(c["args"]) if h else
                          {"error": "UNKNOWN_TOOL",
                           "mensaje": f"usa una de {list(despacho)}"})
                local.append(ToolMessage(
                    json.dumps(salida, ensure_ascii=False)[:800],
                    tool_call_id=c["id"]))
        cierre = get_model("agente-rapido", temperature=0)
        inf = cierre.with_structured_output(Informe).invoke(
            local + [HumanMessage(CIERRE)])
        print(json.dumps({"nodo": nombre, "entrada": entrada,
                          "hechos": len(inf.hechos),
                          "devuelve": not inf.resuelto},
                         ensure_ascii=False))
        return Command(
            goto="supervisor",
            update={"hechos": [{"autor": nombre, "dato": d}
                               for d in inf.hechos],
                    "devuelto_por": None if inf.resuelto
                    else f"{nombre}: {inf.me_falta}"},
        )

    return nodo


FACTURACION = """Especialista de facturación de Meridiano.
Compruebas importes, recibos y duplicados. No hablas con el
cliente y no abres disputas: eso es de fraude."""

FRAUDE = """Especialista de fraude de Meridiano. Localizas cargos
no reconocidos y abres disputas cuando procede. No devuelves
dinero y no hablas con el cliente."""

RESPONDER = """Redactas la respuesta al cliente de Meridiano con
los hechos dados y nada más. Si algo quedó sin resolver, dilo y di
qué necesitas de él para seguir."""


def responder(estado: EstadoMeridiano) -> Command[Literal["__end__"]]:
    texto = get_model("agente-equilibrado").invoke(
        [SystemMessage(RESPONDER),
         HumanMessage(briefing(estado))]).text
    return Command(goto=END, update={"respuesta": texto})


g = StateGraph(EstadoMeridiano)
g.add_node("supervisor", supervisor)
g.add_node("facturacion", trabajador(
    "facturacion", FACTURACION,
    [buscar_transferencia, buscar_duplicados]))
g.add_node("fraude", trabajador(
    "fraude", FRAUDE, [historial_cliente, abrir_disputa]))
g.add_node("responder", responder)
g.add_edge(START, "supervisor")
# Ni una sola add_edge entre el supervisor y los trabajadores: esas
# aristas las declara el Literal del tipo de retorno de cada nodo.
app = g.compile()

if __name__ == "__main__":
    final = app.invoke({
        "cliente": "C-99", "referencia": "REF-4471",
        "consulta": "Me han cobrado dos veces el alquiler y además "
                    "hay un cargo de 49,90 que no reconozco.",
        "hechos": [], "encargo": "Clasifica y reparte.",
        "devuelto_por": None, "saltos": 0, "respuesta": "",
    })
    print(final["respuesta"])
