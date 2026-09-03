from typing import Literal
from pydantic import BaseModel

class ActionRequest(BaseModel):
    subject_id: str
    action: str
    resource: str
    risk_tier: str
    amount_eur: float | None = None
    context: dict

class PolicyDecision(BaseModel):
    allow: bool
    require_human: bool
    reasons: list[str]

def authorize_action(req: ActionRequest) -> PolicyDecision:
    if req.risk_tier == "irreversible_high":
        return PolicyDecision(
            allow=True,
            require_human=True,
            reasons=["acciones irreversibles exigen aprobación humana"],
        )
    if req.amount_eur and req.amount_eur > 100:
        return PolicyDecision(
            allow=False,
            require_human=True,
            reasons=["importe supera límite autónomo"],
        )
    return PolicyDecision(allow=True, require_human=False, reasons=[])


# --- costura PENDIENTE del M35.2 (extraer_meridiano) ---
# PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta.
# El script no la aplica en su sitio: eso es una decision. Ver COSTURAS.md.
decision = policy_engine.authorize({
  'subject': {'user_id': 'C-99', 'auth_level': 'strong'},
  'agent': {'id': 'meridiano.chat.support', 'version': '4.2.1'},
  'tool': {'id': 'core.accounts.read_movements', 'kind': 'read'},
  'resource': {'account_owner': 'C-99', 'data_class': 'confidential'},
  'context': {'purpose': 'customer_support', 'env': 'prod'},
  'risk': {'autonomy_level': 'L0'}
})
# allow | deny | require_human | require_dry_run | require_step_up_auth
