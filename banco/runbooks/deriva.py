# runbooks/deriva.py --- la deriva del 28.3 como código: la
# consulta del runbook, con su umbral y su ventana. Lo lanza el
# scheduler cada hora, desde la raíz del repo y como MÓDULO, que
# es lo que pone la raíz en el path:
#   0 * * * *  cd /srv/banco && uv run python -m runbooks.deriva
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg

from evals.medidas import casos_para, margen   # el 15.7
from trazas import MUESTREO                    # el 36.6

AGENTE = "chat.support"
SLO = 0.92        # el piso del 28.1; la puerta del 18.4 es otra
CAIDA = 0.02      # a 0,90 el sistema ya no pasaría su release
TIER = "L1"       # el `risk_tier` del `agent.yaml` del 32.3
HORAS = 168       # una semana, como el SLO que vigila
# La ventana se elige en CASOS y luego se traduce a horas. El
# intervalo de esos dos puntos sobre 0,92 se cierra con 707
# runs juzgados, y al 10% de muestreo del 36.3 son 7.070 de
# tráfico. Ojo con lo que compra la cifra: es el SUELO para
# comparar dos ventanas, y con ella una caída de exactamente
# dos puntos dispara el 55% de las semanas. Nueve de cada
# diez piden unas 2.000 juzgadas, y `casos_para_detectar`
# hace esa cuenta para la regla del 15.7. Las palancas
# siguen siendo alargar la ventana o declarar una caída
# mayor, y la segunda es cuadrática: cinco puntos bajan a
# 114 juzgados.
MINIMOS = casos_para(CAIDA, SLO)
TRAFICO = round(MINIMOS / MUESTREO[TIER])

CONSULTA = """
SELECT count(*) AS n,
       avg(("eval.scores"->>'faithfulness')::float) AS media
FROM lake.trazas
WHERE "agent.id" = %(agente)s AND "env" = 'prod'
  AND "agent.version" = %(version)s
  AND "eval.sampled" = 'true'
  AND "eval.scores"->>'faithfulness' IS NOT NULL
  AND ts >= %(desde)s AND ts < %(hasta)s
"""


def ventana(cur, version: str, fin: datetime) -> tuple:
    cur.execute(CONSULTA, {"agente": AGENTE, "version": version,
                           "desde": fin - timedelta(hours=HORAS),
                           "hasta": fin})
    n, media = cur.fetchone()
    return n, float(media or 0.0)


def estado(cur, version: str) -> str:
    """Dos preguntas, y las dos abren el runbook. La del suelo
    absoluto va primera porque ve lo que la otra no puede ver:
    media décima por semana nunca supera el ruido entre dos
    ventanas seguidas y se lleva el trimestre entero."""
    fin = datetime.now(timezone.utc)
    n1, m1 = ventana(cur, version, fin)
    n0, m0 = ventana(cur, version, fin - timedelta(hours=HORAS))
    if min(n0, n1) < MINIMOS:
        # El tercer veredicto del 15.7: por debajo de esta n, la
        # diferencia entre las dos medias es azar con formato.
        return f"SIN MUESTRA n={n0},{n1} pide {MINIMOS}/{TRAFICO}"
    suelo = max(margen(m0, n0), margen(m1, n1))
    if m1 + margen(m1, n1) < SLO:
        return f"SLO {m1:.3f} < {SLO} n={n1}"
    if m0 - m1 > suelo:
        return f"DERIVA {m0:.3f}->{m1:.3f} +-{suelo:.3f}"
    return f"OK {m0:.3f}->{m1:.3f} +-{suelo:.3f}"


if __name__ == "__main__":
    with psycopg.connect(os.environ["LAKE_URL"]) as lago:
        cur = lago.cursor()
        # Una línea por VERSIÓN publicada: promediar la flota
        # mezcla el despliegue de ayer con la deriva de la
        # semana, y entonces todo parece deriva.
        cur.execute('SELECT DISTINCT "agent.version" FROM'
                    ' lake.trazas WHERE "agent.id" = %s AND ts >='
                    ' now() - %s::interval',
                    (AGENTE, f"{2 * HORAS} hours"))
        filas = {v: estado(cur, v) for (v,) in cur.fetchall()}
    for v, e in sorted(filas.items()):
        print(f"{AGENTE}@{v:<8} {e}")
    sys.exit(0 if all(e.startswith(("OK", "SIN"))
                      for e in filas.values()) else 1)
