# mcp_core.py --- el core del banco expuesto por MCP: las tablas
# de negocio del 7.6, y nada más que ellas.
import logging
import os

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

log = logging.getLogger("mcp.core")
POOL = ConnectionPool(os.environ["DATABASE_URL"], open=True,
                      kwargs={"options": "-c search_path=banco"})
# El path por defecto ya es /mcp. De stateless_http, más abajo.
mcp = FastMCP("banco-core", stateless_http=True,
              host="0.0.0.0", port=8081)


def _filas(sql: str, args: tuple) -> list[dict]:
    log.info("%s %s", sql[:30], args)       # criterio del Ej. 10.1
    with POOL.connection() as cx, cx.cursor(row_factory=dict_row) as c:
        c.execute(sql, args)
        return c.fetchall()


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def historial_cuenta(iban: str, dias: int = 7) -> dict:
    """Movimientos recientes de un IBAN. Úsala para confirmar un
    duplicado: mismo importe y beneficiario, minutos. dias <= 90."""
    if dias > 90:
        return {"error": "INVALID_ARGUMENT", "mensaje": "dias <= 90"}
    if not _filas("SELECT 1 FROM cuentas WHERE iban = %s", (iban,)):
        return {"error": "NOT_FOUND", "mensaje": f"sin cuenta {iban}"}
    movs = _filas("SELECT referencia, importe_cent, beneficiario FROM"
                  " transferencias WHERE iban_ordenante = %s AND"
                  " creada_en > now() - make_interval(days => %s)",
                  (iban, dias))
    for m in movs:            # decisión 6 del 3.2: el dinero es código
        cent = m.pop("importe_cent")
        m["importe"] = f"{cent // 100},{cent % 100:02d} EUR"
    return {"iban": iban, "movimientos": movs}


@mcp.tool(annotations=ToolAnnotations(idempotentHint=True))
def abrir_incidencia(referencia: str, motivo: str) -> dict:
    """Abre una incidencia de back-office sobre una transferencia.
    Idempotente: si ya hay una viva para esa referencia devuelve esa
    y no abre otra."""
    if not _filas("SELECT 1 FROM transferencias WHERE referencia"
                  " = %s", (referencia,)):
        return {"error": "NOT_FOUND",
                "mensaje": f"sin transferencia {referencia}"}
    f = _filas("INSERT INTO incidencias (referencia, motivo) VALUES"
               " (%s, %s) ON CONFLICT DO NOTHING RETURNING id",
               (referencia, motivo))
    viva = f or _filas("SELECT id FROM incidencias WHERE referencia"
                       " = %s AND estado <> 'resuelta'",
                       (referencia,))
    return {"ok": True, "id": viva[0]["id"], "duplicada": not f}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run(transport="streamable-http")   # guion, no guion bajo
