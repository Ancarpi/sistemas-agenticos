# herramientas.py --- las cuatro del 3.3, con el esquema generado.
# El cuerpo no se toca ni se copia: sigue en nano_agent.py, que se
# queda sin framework porque esa es su tesis. Aquí solo se añade
# la superficie que create_agent sabe leer.
from typing import Annotated

from langchain_core.tools import tool

import nano_agent as core          # el fichero del 3.3, intacto


@tool
def buscar_transferencia(
    referencia: Annotated[str, "Formato REF-NNNN"],
) -> dict:
    """Datos de una transferencia SEPA por referencia. Primer paso
    de toda incidencia; nunca supongas importes."""
    return core.buscar_transferencia(referencia)


@tool
def historial_cuenta(
    iban: Annotated[str, "IBAN español, 24 caracteres"],
    dias: Annotated[int, "Ventana en días, de 1 a 90"] = 7,
) -> dict:
    """Movimientos recientes de un IBAN. Úsala para confirmar un
    duplicado: mismo importe y beneficiario, minutos."""
    return core.historial_cuenta(iban, dias)


@tool
def marcar_resuelta(
    referencia: Annotated[str, "Formato REF-NNNN"],
    motivo: Annotated[str, "Una frase, va a auditoría"],
) -> dict:
    """Cierra la incidencia. SOLO si no hay dinero que mover ni
    cliente al que avisar."""
    return core.marcar_resuelta(referencia, motivo)


@tool
def escalar_a_humano(
    referencia: Annotated[str, "Formato REF-NNNN"],
    resumen: Annotated[str, "Qué pasó y qué propones"],
) -> dict:
    """Manda el caso a la cola N2. Úsala si hay que devolver
    dinero, faltan datos o queda duda razonable."""
    return core.escalar_a_humano(referencia, resumen)
