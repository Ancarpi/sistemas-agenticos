# nano_agent.py --- back-office del banco, sin framework de agentes.
import json
import time
from datetime import datetime, timedelta

from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ToolMessage,
)

from src.core.models import get_model      # la fábrica del 0.4

# El corte que el 9.2 promete empieza aquí: de `IBAN_CLIENTE` a
# `eur()` van treinta líneas que no son del agente, y son
# `src/core/banco.py`, el fichero que allí se importa con
# `from src.core.banco import TRANSFERENCIAS, eur`. Lo que sigue
# a `eur()` es `nano_agent.py`, y arranca con
# `from src.core.banco import CASOS, TRANSFERENCIAS, eur, hace`.
IBAN_CLIENTE = "ES9121000418450200051332"

# El «core bancario» de este capítulo: un dict. En el M11 será
# Postgres, y el loop no cambiará ni una línea.
AHORA = datetime.now()


def hace(**delta) -> str:
    """La semilla cuelga del reloj: con la fecha escrita en duro
    caduca sola y historial_cuenta se queda sin movimientos."""
    return (AHORA - timedelta(**delta)).isoformat(timespec="seconds")


TRANSFERENCIAS = {
    "REF-4471": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler mensual",
                 "fecha": hace(hours=3, seconds=19)},
    "REF-4472": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler mensual",
                 # La gemela, 19 segundos después: ese hueco es
                 # todo lo que distingue un doble envío.
                 "fecha": hace(hours=3)},
    "REF-4468": {"iban": IBAN_CLIENTE, "importe_cent": 4990,
                 "beneficiario": "ES4814650100722030876293",
                 "concepto": "Cuota gimnasio",
                 "fecha": hace(days=1)},
}
CASOS: dict = {}          # el único efecto lateral del agente


def eur(cent: int) -> str:
    """Decisión 6: formatear dinero es código, nunca una llamada."""
    signo, cent = ("-" if cent < 0 else ""), abs(cent)
    return f"{signo}{cent // 100},{cent % 100:02d} EUR"


def buscar_transferencia(referencia: str) -> dict:
    t = TRANSFERENCIAS.get(referencia)
    if t is None:
        # Error ESPERABLE: no revienta, vuelve al modelo como dato.
        return {"error": "NOT_FOUND",
                "mensaje": f"No existe {referencia}; formato REF-NNNN"}
    return {"referencia": referencia, "importe": eur(t["importe_cent"]),
            **{k: v for k, v in t.items() if k != "importe_cent"}}


def historial_cuenta(iban: str, dias: int = 7) -> dict:
    if dias > 90:
        return {"error": "INVALID_ARGUMENT",
                "mensaje": "dias <= 90; más allá no hay retención"}
    # El filtro que hacía falta para que `dias` signifique algo
    # y para que el docstring de `hace()` sea verdad: las cadenas
    # ISO con el mismo `timespec` se ordenan como fechas.
    desde = hace(days=dias)
    movs = [{"referencia": r, "importe": eur(t["importe_cent"]),
             "fecha": t["fecha"], "beneficiario": t["beneficiario"]}
            for r, t in TRANSFERENCIAS.items()
            if t["iban"] == iban and t["fecha"] >= desde]
    return {"iban": iban, "dias": dias, "movimientos": movs}


def marcar_resuelta(referencia: str, motivo: str) -> dict:
    CASOS[referencia] = {"estado": "resuelta", "motivo": motivo}
    return {"ok": True, "referencia": referencia}


def escalar_a_humano(referencia: str, resumen: str) -> dict:
    CASOS[referencia] = {"estado": "escalada", "resumen": resumen}
    return {"ok": True, "cola": "backoffice-n2", "sla_horas": 4}
# Esto es EL VELO. create_agent genera este JSON Schema por ti a
# partir de la firma y el docstring; aquí lo escribes tú, porque es
# literalmente lo único que el modelo sabe de tus herramientas.
HERRAMIENTAS = [
    {"type": "function", "function": {
        "name": "buscar_transferencia",
        "description": (
            "Datos de una transferencia SEPA por referencia. Primer "
            "paso de toda incidencia; nunca supongas importes."),
        "parameters": {
            "type": "object",
            "properties": {
                "referencia": {"type": "string",
                               "description": "Formato REF-NNNN"}},
            "required": ["referencia"],
            "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "historial_cuenta",
        "description": (
            "Movimientos recientes de un IBAN. Úsala para confirmar "
            "un duplicado: mismo importe y beneficiario, minutos."),
        "parameters": {
            "type": "object",
            "properties": {
                "iban": {"type": "string",
                         "description": "IBAN español, 24 caracteres"},
                "dias": {"type": "integer", "minimum": 1,
                         "maximum": 90, "default": 7}},
            "required": ["iban"],
            "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "marcar_resuelta",
        "description": (
            "Cierra la incidencia. SOLO si no hay dinero que mover "
            "ni cliente al que avisar."),
        "parameters": {
            "type": "object",
            "properties": {
                "referencia": {"type": "string"},
                "motivo": {"type": "string",
                           "description": "Una frase, va a auditoría"}},
            "required": ["referencia", "motivo"],
            "additionalProperties": False}}},
    {"type": "function", "function": {
        "name": "escalar_a_humano",
        "description": (
            "Manda el caso a la cola N2. Úsala si hay que devolver "
            "dinero, faltan datos o queda duda razonable."),
        "parameters": {
            "type": "object",
            "properties": {
                "referencia": {"type": "string"},
                "resumen": {"type": "string",
                            "description": "Qué pasó y qué propones"}},
            "required": ["referencia", "resumen"],
            "additionalProperties": False}}},
]

DESPACHO = {f.__name__: f for f in (
    buscar_transferencia, historial_cuenta,
    marcar_resuelta, escalar_a_humano)}
SISTEMA = """Eres el agente de back-office del banco.
Investigas incidencias de transferencias SEPA y las cierras o las
escalas. No afirmes nada que no venga de una herramienta. Cierra
solo si no hay dinero que mover. Ante duda, escala. Termina con un
párrafo para el expediente."""


def ejecutar(nombre: str, args: dict) -> str:
    """Decisión 2: el error esperable vuelve al modelo; el de
    sistema (DB caída) sube y lo reintenta el planificador."""
    if nombre not in DESPACHO:
        return json.dumps(
            {"error": "NO_TOOL",
             "mensaje": f"No existe {nombre}; usa una de "
                        f"{list(DESPACHO)}"}, ensure_ascii=False)
    try:
        return json.dumps(DESPACHO[nombre](**args), ensure_ascii=False)
    except TypeError as err:
        return json.dumps({"error": "INVALID_ARGUMENT",
                           "mensaje": str(err)}, ensure_ascii=False)


def nano_agent(tarea: str, max_pasos: int = 8,
               max_tokens: int = 12_000) -> str:
    # bind_tools con dicts NO genera nada: los adjunta tal cual.
    modelo = get_model("agente-rapido", temperature=0)
    modelo = modelo.bind_tools(HERRAMIENTAS)
    estado = [SystemMessage(SISTEMA), HumanMessage(tarea)]
    gastados, firmas = 0, []

    for paso in range(1, max_pasos + 1):
        t0 = time.perf_counter()
        r: AIMessage = modelo.invoke(estado)
        estado.append(r)
        # Sumamos el total de CADA llamada, no el de la última: el
        # contexto entero se reenvía cada vuelta, y eso es lo que
        # pagas. Por eso el gasto de un agente crece cuadrático.
        gastados += (r.usage_metadata or {}).get("total_tokens", 0)
        print(json.dumps({                      # decisión 5
            "paso": paso, "tokens_acum": gastados,
            "ms": round((time.perf_counter() - t0) * 1000),
            "tools": [c["name"] for c in r.tool_calls],
        }, ensure_ascii=False))

        if not r.tool_calls:                    # parada natural
            return r.text
        if gastados > max_tokens:               # decisión 1
            return "PARADA: presupuesto de tokens agotado."

        # Decisión 3: secuencial a propósito. Dos escrituras sobre
        # el mismo caso en paralelo son una carrera; paralelizaría
        # con asyncio.gather solo un lote de lecturas puras.
        for c in r.tool_calls:
            firma = c["name"] + json.dumps(c["args"], sort_keys=True)
            if firmas.count(firma) >= 2:        # bucle educado
                salida = ("Ya has llamado dos veces a esto con los "
                          "mismos argumentos. Cambia de estrategia "
                          "o escala el caso.")
            else:
                salida = ejecutar(c["name"], c["args"])
            firmas.append(firma)
            # Decisión 4: se recorta ANTES de entrar al estado. Una
            # herramienta charlatana no se arregla luego.
            estado.append(ToolMessage(salida[:1200],
                                      tool_call_id=c["id"]))

    return f"PARADA: {max_pasos} pasos sin conclusión; caso abierto."


if __name__ == "__main__":
    print(nano_agent(
        "La transferencia REF-4471 aparece duplicada según el "
        "cliente. Investiga y resuelve o escala."))
    print(json.dumps(CASOS, ensure_ascii=False, indent=2))
