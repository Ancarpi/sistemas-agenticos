from typing import Literal

from langgraph.runtime import get_runtime   # el ctx del 37.2
from pydantic import BaseModel

from src.core.politica import autorizar     # el motor del 26.5

class BloqueoTarjetaPlan(BaseModel):
    masked_pan: str
    reason: Literal["robo", "fraude", "perdida"]
    evidence: list[str]
    customer_message: str

@tool
def bloquear_tarjeta_dry_run(plan: BloqueoTarjetaPlan) -> dict:
    """Valida si el bloqueo sería permitido. No modifica el core."""
    # La decisión la toma el `autorizar` del 26.5, que entra
    # con el dict de seis claves del 35.2 y sale con UNA de sus
    # cinco cadenas; aquí solo se rellena la petición. El ctx es
    # el mismo `context=` que lee el `despachar` del 37.2.
    ctx = get_runtime().context
    decision = autorizar({
        "subject": {"user_id": ctx["humano"]["id"],
                    "auth_level": ctx["humano"]["auth"]},
        "agent": ctx["agente"], "tool": {"id": "core.cards.block"},
        "resource": {"account_owner": ctx["sujeto"],
                     "data_class": "confidential"},
        "context": {"purpose": ctx["proposito"],
                    "env": ctx["entorno"]},
        "risk": {"autonomy_level": "L4"}})   # el 20.1, y Anexo H
    return {"decision": decision,
            "impacto": cards_core.simular(plan.masked_pan)}

@tool
def bloquear_tarjeta_commit(
    plan: BloqueoTarjetaPlan, idempotency_key: str
) -> dict:
    """Bloquea tarjeta tras aprobación y validación. Acción irreversible."""
    with transaction() as tx:
        existing = tx.find_idempotency(idempotency_key)
        if existing:
            return existing.result
        result = cards_core.block(plan.masked_pan, plan.reason)
        tx.outbox("card.blocked", result)
        tx.audit("bloquear_tarjeta", masked(plan), summary(result))
        tx.save_idempotency(idempotency_key, result)
        return result
