from typing import Literal
from pydantic import BaseModel

class BloqueoTarjetaPlan(BaseModel):
    masked_pan: str
    reason: Literal["robo", "fraude", "perdida"]
    evidence: list[str]
    customer_message: str

@tool
def bloquear_tarjeta_dry_run(plan: BloqueoTarjetaPlan) -> dict:
    """Valida si el bloqueo sería permitido. No modifica el core."""
    d = policy_engine.authorize({"action": "cards.block",
                                 "context": plan.model_dump()})
    return {"allowed": d.allow, "reasons": d.reasons}

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
