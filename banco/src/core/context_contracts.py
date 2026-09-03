# src/core/context_contracts.py
from pydantic import BaseModel, Field
from typing import Literal

class ContextContract(BaseModel):
    node: str
    objective: str
    allowed_state_keys: list[str]
    forbidden_patterns: list[str] = Field(default_factory=list)
    visible_tools: list[str]
    output_schema: str | None
    max_input_tokens: int
    max_output_tokens: int
    latency_budget_ms: int
    max_cost_eur: float
    fallback: Literal["retry", "escalate", "abort", "degrade"]

TRIAGE_CONTRACT = ContextContract(
    node="triage_sepa",
    objective="clasificar incidencia sin ejecutar acciones",
    allowed_state_keys=["referencia", "descripcion_anon", "eventos"],
    forbidden_patterns=[r"\bES\d{2}(?:[ -]?\d{4}){5}\b",
                        r"\b(?:\d[ -]?){16}\b"],
    visible_tools=[],
    output_schema="TriageIncidencia",
    max_input_tokens=1200,
    max_output_tokens=300,
    latency_budget_ms=2000,
    max_cost_eur=0.002,
    fallback="escalate",
)
