from typing import Literal
from pydantic import BaseModel

class ToolError(BaseModel):
    code: Literal[
        "INVALID_ARGUMENT", "NOT_FOUND", "AUTHZ_DENIED",
        "PRECONDITION_FAILED", "TRANSIENT_UPSTREAM",
        "PERMANENT_UPSTREAM", "POLICY_BLOCKED"
    ]
    safe_message: str
    retryable: bool
    suggested_next_step: str | None = None

# Ejemplo devuelto como ToolMessage, no como excepción cruda.
ToolError(
    code="PRECONDITION_FAILED",
    safe_message="La tarjeta ya está bloqueada desde el 1 de julio de 2026.",
    retryable=False,
    suggested_next_step="Informa al cliente y ofrece abrir un ticket."
)


# --- anadido del M22.3 (extraer_banco) ---
# HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro.
from typing import Literal
from pydantic import BaseModel

class HumanHandoffPacket(BaseModel):
    conversation_id: str
    customer_id: str | None
    reason: Literal[
        "low_confidence", "policy", "user_requested",
        "complaint", "sensitive_action", "tool_failure"
    ]
    verified_facts: list[str]
    unresolved_questions: list[str]
    tools_used: list[str]
    proposed_next_action: str
    risk_flags: list[str]
    trace_url: str | None


# --- anadido del M23.1 (extraer_banco) ---
# HandoffContract y su campo authority: la frontera entre agentes.
from typing import Literal
from pydantic import BaseModel

class HandoffContract(BaseModel):
    from_agent: str
    to_agent: str
    task: str
    authority: Literal["recommend", "prepare", "execute", "approve"]
    facts: list[str]
    assumptions: list[str]
    open_questions: list[str]
    permitted_tools: list[str]
    forbidden_actions: list[str]
    required_output_schema: str
    return_to: str | None
