# agente_backoffice.py --- el nano_agent del 3.3, industrializado.
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware, ModelCallLimitMiddleware,
    ModelRetryMiddleware, PIIMiddleware, SummarizationMiddleware,
)

from src.core.models import get_model             # la fábrica del 0.4
# Del 3.3 vienen el prompt y el core; las herramientas llegan ya
# decoradas del 4.1, porque create_agent exige el docstring.
from nano_agent import SISTEMA as PROMPT_BACKOFFICE, TRANSFERENCIAS
from herramientas import (
    buscar_transferencia, devolver_transferencia, escalar_a_humano,
    historial_cuenta, marcar_resuelta,   # devolver_ es la del Ej. 3.1
)

# ES + 2 dígitos de control + 20. El regex solo tiene que ENCONTRAR
# el IBAN; el mod-97 lo valida tu código (decisión 6 del 3.2).
IBAN_ES = r"\bES\d{2}(?:[ -]?\d{4}){5}\b"


def supera_umbral(peticion) -> bool:
    """El importe se lee del core, NUNCA del argumento que escribe
    el modelo: si no, para saltarse el visto bueno le basta con
    declarar que devuelve un euro."""
    ref = peticion.tool_call["args"].get("referencia", "")
    return TRANSFERENCIAS.get(ref, {}).get("importe_cent", 0) >= 5_000


def tarjeta_n2(tool_call, state, runtime) -> str:
    """Lo que lee el aprobador. Indexa directo porque solo se llama
    cuando `when` ya confirmó que la referencia existe. Esto se
    persiste en el checkpoint: escribe aquí solo lo que aceptarías
    conservar seis años."""
    ref = tool_call["args"]["referencia"]
    cent = TRANSFERENCIAS[ref]["importe_cent"]
    return (f"Devolución SEPA {ref} por {cent // 100},{cent % 100:02d}"
            f" EUR\nMotivo del agente: {tool_call['args']['motivo']}")


MIDDLEWARE = [
    # 1 --- PII PRIMERO. hash y no mask: mask conserva los cuatro
    # últimos dígitos (****7892), que son dato personal y además
    # colapsan dos beneficiarios distintos que acaben igual; el
    # hash no filtra nada y sigue siendo determinista, así que el
    # agente detecta «mismo beneficiario» sin tener el IBAN.
    PIIMiddleware(
        "iban", strategy="hash", detector=IBAN_ES,
        apply_to_input=True,         # el mensaje del cliente
        apply_to_tool_results=True,  # el core: por AQUÍ entra
        apply_to_output=True,        # lo que redacta el modelo
    ),
    # 2 --- Resumen con el alias BARATO: resumir no razona. Misma
    # cifra que el techo del 3.3, pero aquí es tamaño de contexto,
    # no gasto acumulado: allí paraba, aquí dispara un resumen.
    SummarizationMiddleware(
        model=get_model("agente-rapido"),
        trigger=("tokens", 12_000),
        keep=("messages", 8),        # ~4 vueltas completas
    ),
    # 3 --- La decisión 1 del 3.2, ya industrializada.
    ModelCallLimitMiddleware(thread_limit=40, run_limit=8,
                             exit_behavior="end"),
    # 4 --- max_retries=1, no el 2 por defecto: el gateway ya
    # reintenta dos veces (num_retries del 0.5) y encima cae al
    # fallback. El 2 por defecto son 3x3 = 9 llamadas al proveedor
    # por vuelta perdida.
    ModelRetryMiddleware(max_retries=1, initial_delay=2.0,
                         on_failure="error"),
    # 5 --- El humano el ÚLTIMO: after_model recorre la lista al
    # revés, y quieres que vea la respuesta antes que nadie.
    HumanInTheLoopMiddleware(
        interrupt_on={
            "devolver_transferencia": {
                "allowed_decisions": ["approve", "edit", "reject"],
                "description": tarjeta_n2,
                # Por debajo de 50 EUR no despiertas a nadie.
                "when": supera_umbral,
            },
            "marcar_resuelta": {
                "allowed_decisions": ["approve", "reject"]},
            "escalar_a_humano": False,     # explícito: no interrumpe
            "buscar_transferencia": False,
            "historial_cuenta": False,
        },
        description_prefix="Back-office N2",
    ),
]


def construir_agente(cp):
    """El checkpointer entra por parámetro y no es opcional: sin él
    no hay reanudar, y quien lo abre es el bloque de abajo."""
    return create_agent(
        model=get_model("agente-listo", reasoning_effort="medium"),
        tools=[buscar_transferencia, historial_cuenta,
               marcar_resuelta, escalar_a_humano,
               devolver_transferencia],
        system_prompt=PROMPT_BACKOFFICE,
        middleware=MIDDLEWARE,
        checkpointer=cp,
    )
