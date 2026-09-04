# src/finops/coste_por_resolucion.py --- la métrica del 28.1,
# calculada. Entran las trazas de cada llamada y el desenlace de
# cada caso; salen coste por caso, por resolución correcta y por
# escalado, en una sola moneda.
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import httpx
import psycopg

# La tarifa va CONGELADA con la fecha en el nombre, como el
# conjunto dorado del 15.7: recalcular marzo con el precio de hoy
# no corrige la serie, la inventa. La escribe `congelar()` desde
# el gateway del 0.5, porque el precio se le pregunta a quien
# cobra (11.5).
FECHA_TARIFA = "2026-09-01"        # el día de la corrida del 11.5
TARIFA = Path("config") / f"tarifa.{FECHA_TARIFA}.json"
CADUCIDAD = 90                     # días
# Los tres multiplicadores del 15.5, que describen la forma de la
# factura y por eso viven aquí y no en la tarifa. Escribir la
# caché lleva RECARGO (1,25 con vigencia de cinco minutos, el
# doble con una hora); leerla, descuento; y el batch descuenta
# sobre entrada y salida a la vez.
ESCRITURA, LECTURA, BATCH = 1.25, 0.10, 0.50
# El caso que acaba en humano: siete minutos a 36 EUR/hora (31.3),
# la media del banco. El día que la cola de aprobación registre el
# reloj de verdad, esta constante sobra.
EUR_HUMANO = 36.0 / 60 * 7
# Las tres que ningún gateway sabe y nadie debe adivinar.
A_MANO = ("usd_eur", "herramienta_usd", "rerank_usd")


def tarifa() -> dict:
    """Precio por millón de tokens por alias del 0.5, más las tres
    de `A_MANO`. Revienta por ellas en vez de colar un cero, que
    se publicaría como si fuera una medida."""
    if not TARIFA.exists():
        raise SystemExit(f"falta {TARIFA}: corre congelar()")
    dias = (date.today() - date.fromisoformat(FECHA_TARIFA)).days
    if dias > CADUCIDAD:
        raise SystemExit(f"tarifa de hace {dias} días; recongela")
    t = json.loads(TARIFA.read_text())
    faltan = [k for k in A_MANO if t.get(k) is None]
    if faltan:
        raise SystemExit(f"rellena a mano: {', '.join(faltan)}")
    return t


def congelar() -> None:
    """Lo que el gateway sí sabe. Deja a null las tres de
    `A_MANO`: el cambio lo fija tu tesorería, la llamada al core
    la factura quien te la sirve, y el reranker del 8.2 se cobra
    por búsqueda y no por token."""
    base = os.environ["OPENAI_API_BASE"].removesuffix("/v1")
    r = httpx.get(f"{base}/model/info", headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    t: dict = {k: None for k in A_MANO}
    for m in r.json()["data"]:
        i = m["model_info"]
        t[m["model_name"]] = {
            "entrada": (i.get("input_cost_per_token") or 0) * 1e6,
            "salida": (i.get("output_cost_per_token") or 0) * 1e6}
    TARIFA.parent.mkdir(parents=True, exist_ok=True)
    TARIFA.write_text(json.dumps(t, indent=1, sort_keys=True))


@dataclass(frozen=True)
class Llamada:
    """Una llamada facturable con el caso al que se imputa, sacado
    del `thread.id` del 36.1 (`inc-REF-4471`): una traza sin clave
    de negocio se deja sumar, pero no dividir, y esto es una
    división. `nueva` son los tokens de entrada que NO estaban
    cacheados; si tu proveedor los reporta incluidos, réstalos
    aquí o pagarás el prefijo dos veces."""
    caso: str
    alias: str
    nueva: int
    escrita: int
    leida: int
    salida: int
    batch: bool = False
    herramientas: int = 0    # llamadas al core en este paso
    reranks: int = 0


def coste_usd(ll: Llamada, t: dict) -> float:
    """Una llamada, con la caché en sus dos precios. El KeyError
    del alias es deliberado: un modelo sin tarifa para la corrida
    entera, y no se estima."""
    dentro = (ll.nueva + ll.escrita * ESCRITURA
              + ll.leida * LECTURA) * t[ll.alias]["entrada"] / 1e6
    modelo = dentro + ll.salida * t[ll.alias]["salida"] / 1e6
    return (modelo * (BATCH if ll.batch else 1.0)
            + ll.herramientas * t["herramienta_usd"]
            + ll.reranks * t["rerank_usd"])


CASOS = """SELECT referencia,
       bool_or(estado = 'resuelta') AS cerrado,
       bool_or(cola IS NOT NULL)    AS humano,
       count(*) > 1                 AS reabierto
  FROM banco.incidencias
 WHERE abierta_en >= %s AND abierta_en < %s
 GROUP BY referencia"""


def desenlaces(cur, desde: date, hasta: date) -> dict:
    """Qué pasó con cada caso, del esquema del 7.6 y sin columna
    nueva: el índice único parcial de allí solo deja una
    incidencia viva por referencia, así que una segunda fila ES
    una reapertura."""
    cur.execute(CASOS, (desde, hasta))
    return {f[0]: {"cerrado": f[1], "humano": f[2],
                   "reabierto": f[3]} for f in cur.fetchall()}


def metrica(llamadas, casos: dict, t: dict) -> dict:
    """La división del título. El denominador son las resoluciones
    CORRECTAS del 28.1, cerradas sin humano y sin reapertura; el
    numerador, el coste entero de la ventana. Escalados, huérfanos
    y reabiertos siguen dentro y los pagan las que salieron bien,
    que es lo que encarece al agente que contesta mal y barato."""
    gasto = {ref: 0.0 for ref in casos}
    # Coste que no se imputa a ningún caso de la ventana: sondas,
    # reintentos, `thread_id` mal formados. Sacarlo del numerador
    # es la forma cómoda de que la métrica salga bien.
    huerfano = 0.0
    for ll in llamadas:
        eur = coste_usd(ll, t) * t["usd_eur"]
        if ll.caso in gasto:
            gasto[ll.caso] += eur
        else:
            huerfano += eur
    correctas, escalados = [], []
    for ref, c in casos.items():
        if c["humano"]:
            escalados.append(gasto[ref] + EUR_HUMANO)
        elif c["cerrado"] and not c["reabierto"]:
            correctas.append(gasto[ref])
    humano = len(escalados) * EUR_HUMANO
    total = sum(gasto.values()) + huerfano + humano
    return {"total": total, "huerfano": huerfano,
            "modelo": total - humano, "casos": len(casos),
            "correctas": len(correctas),
            "escalados": len(escalados),
            "por_caso": total / max(len(casos), 1),
            "por_correcta": total / max(len(correctas), 1),
            "por_escalado": sum(escalados) / max(len(escalados), 1)}


def cuadrar(m: dict, t: dict, desde: date, hasta: date) -> str:
    """Contra quien cobra (11.5). El `spend` del gateway es la
    verdad y esta cuenta es una reconstrucción: por encima del 2%
    lo roto es la tarifa o el desglose de caché, y una métrica que
    no cuadra con la factura se quema en el primer comité."""
    base = os.environ["OPENAI_API_BASE"].removesuffix("/v1")
    r = httpx.get(f"{base}/spend/logs", params={
        "start_date": desde.isoformat(),
        "end_date": hasta.isoformat()}, headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    real = sum(f["spend"] for f in r.json()) * t["usd_eur"]
    desvio = abs(m["modelo"] - real) / max(real, 1e-9)
    return (f"CUADRE {m['modelo']:.2f} calculados vs {real:.2f}"
            f" facturados ({desvio:.1%})"
            + ("  publicable" if desvio <= 0.02 else "  NO"))


def main(llamadas, desde: date, hasta: date) -> None:
    t = tarifa()
    with psycopg.connect(os.environ["DATABASE_URL"]) as bd:
        m = metrica(llamadas, desenlaces(bd.cursor(), desde,
                                         hasta), t)
    print(f"casos {m['casos']}   correctas {m['correctas']}"
          f"   escalados {m['escalados']}\n"
          f"COSTE {m['total']:8.2f} EUR"
          f"   ({m['huerfano']:.2f} sin caso)\n"
          f"  por caso        {m['por_caso']:.4f} EUR\n"
          f"  por RESOLUCION  {m['por_correcta']:.4f} EUR"
          f"   (piso 28.1: 0,08)\n"
          f"  por escalado    {m['por_escalado']:.4f} EUR")
    print(cuadrar(m, t, desde, hasta))
