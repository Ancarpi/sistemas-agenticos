from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class MemoryRecord(BaseModel):
    namespace: tuple[str, ...]        # ('retail', 'soporte', 'C-99')
    key: str                         # 'preferred_language'
    value: dict
    source_run_id: str
    sensitivity: Literal['public','internal','confidential','restricted']
    confidence: float
    ttl_days: int | None
    consent_basis: str | None
    owner: str
    created_at: datetime
    expires_at: datetime | None


# --- costura PENDIENTE del M34.5 (extraer_banco) ---
# PENDIENTE. Las tres APIs tipadas de memoria con sus receipts: los cuerpos son ... y los tres tipos de receipt no existen todavia, asi que el modulo no importa hasta que los escribas.
# El script no la aplica en su sitio: eso es una decision. Ver COSTURAS.md.
@tool
def recordar_preferencia_cliente(
    cliente_id: str,
    clave: Literal['idioma', 'canal_preferido', 'formato_resumen'],
    valor: str,
    evidencia: str,
) -> MemoryWriteReceipt:
    """Guarda una preferencia declarada del cliente, con su evidencia."""
    ...
