# batch_nocturno.py --- el worker entero. Lo arranca el scheduler:
#   0 2 * * *  cd /srv/banco && uv run python batch_nocturno.py
import os
from datetime import date

import httpx
import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

from agente_backoffice import construir_agente   # el del 4.3
from fanout_nocturno import g                    # el `Send` del 6.4

BASE = os.environ["OPENAI_API_BASE"].removesuffix("/v1")
PRESUPUESTO_USD = 8.0     # tope DURO; `spend` llega en dólares
TANDA = 25                # unidades entre dos comprobaciones
AUTO = ("duplicado", "comision")   # lo demás pasa por el agente


def gasto_usd() -> float:
    r = httpx.get(f"{BASE}/key/info", headers={
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
    return r.json()["info"]["spend"]


def candado(cur) -> bool:
    cur.execute("SELECT pg_try_advisory_lock(hashtext('nocturno'))")
    return cur.fetchone()[0]


def cerrar(cur, ref: str, motivo: str) -> bool:
    """La idempotencia va en el WHERE, no en un `if` tuyo."""
    cur.execute("UPDATE banco.incidencias SET estado='resuelta',"
                " motivo=%s, cerrada_en=now() WHERE referencia=%s"
                " AND estado <> 'resuelta'", (motivo, ref))
    return cur.rowcount == 1


def marcar(cur, ref: str, cola: str, motivo: str | None = None):
    cur.execute("UPDATE banco.incidencias SET estado='escalada',"
                " cola=%s, motivo=coalesce(%s, motivo) WHERE"
                " referencia=%s", (cola, motivo, ref))


def main() -> None:
    corte = date.today().isoformat()
    n = {"resueltas": 0, "aprobacion": 0, "dlq": 0, "sin tocar": 0}
    with psycopg.connect(os.environ["DATABASE_URL"]) as bd, \
            PostgresSaver.from_conn_string(
                os.environ["DATABASE_URL"]) as cp:
        cur, gasto_0 = bd.cursor(), gasto_usd()
        if not candado(cur):
            print("otra corrida viva; salgo sin tocar nada")
            return
        cp.setup()
        triaje, agente = g.compile(checkpointer=cp), construir_agente(cp)
        # El lote es una CONSULTA, no el fichero de la noche antes.
        cur.execute("SELECT referencia FROM banco.incidencias"
                    " WHERE estado='abierta' AND abierta_en < %s"
                    " ORDER BY abierta_en", (corte,))
        cola = [f[0] for f in cur.fetchall()]
        for i in range(0, len(cola), TANDA):
            if gasto_usd() - gasto_0 >= PRESUPUESTO_USD:
                n["sin tocar"] = len(cola) - i
                break              # parada LIMPIA, no un `kill`
            # thread_id derivado de la CLAVE, no de la posición: `i`
            # se desplaza al relanzar, porque los casos ya cerrados
            # salen del SELECT y los índices corren. `cola[i]` no
            # se mueve, así que el checkpoint de la tanda que murió
            # se vuelve a direccionar en vez de pagarse otra vez.
            hilo = {"configurable":
                    {"thread_id": f"nocturno-{corte}-{cola[i]}"}}
            # Del estado que vuelve solo se lee `veredictos`: el
            # `informe` que fabrica `reducir` (6.4) se descarta.
            r = triaje.invoke(
                {"referencias": cola[i:i + TANDA], "veredictos": []},
                config={**hilo, "max_concurrency": 5})
            for v in r["veredictos"]:
                ref = v["referencia"]
                if v["categoria"] in AUTO:
                    n["resueltas"] += cerrar(cur, ref, v["categoria"])
                    continue
                # Lo que pide juicio va al agente del 4.3. El worker
                # NO espera: si interrumpe, marca el caso y sigue;
                # si termina, el cierre en Postgres lo hace AQUÍ,
                # porque las herramientas del 3.3 no tocan la tabla.
                h = {"configurable": {"thread_id": f"inc-{ref}"}}
                try:
                    s = agente.invoke({"messages": [(
                        "user", f"Resuelve la incidencia {ref}.")]}, h)
                    if s.get("__interrupt__"):
                        marcar(cur, ref, "aprobacion")
                        n["aprobacion"] += 1
                    else:
                        n["resueltas"] += cerrar(cur, ref, "agente")
                except Exception as e:
                    # Aquí llega YA reintentado: dos veces por el
                    # gateway (0.5) y una por el 4.3. Lo que sigue
                    # vivo hasta este `except` es dead-letter.
                    marcar(cur, ref, "dlq", str(e)[:200])
                    n["dlq"] += 1
            bd.commit()   # una transacción por TANDA: el fallo de
                          # la 17 no deshace las 16 ya cerradas
        print(informe(cur, n, gasto_usd() - gasto_0))


if __name__ == "__main__":
    main()
def informe(cur, n: dict, gasto: float) -> str:
    """Lo que un humano lee a las 8:00. Abre por lo único que
    exige una decisión hoy: el informe que empieza por «390
    resueltas» se lee en diagonal, y también el día que importa."""
    cur.execute("SELECT referencia, motivo FROM"
                " banco.incidencias WHERE cola='aprobacion'"
                " ORDER BY abierta_en")
    espera = cur.fetchall()
    hechas = sum(n.values()) - n["sin tocar"]
    filas = [f"APROBACIÓN PENDIENTE ({len(espera)}); el hilo de"
             f" cada una sigue vivo en el checkpoint"]
    filas += [f"  inc-{r}  {m[:46]}" for r, m in espera[:5]]
    filas += [f"{k:>12} {v:>5}" for k, v in n.items()]
    filas.append(f"COSTE {gasto:6.2f} USD de {PRESUPUESTO_USD:.2f}"
                 f"   ({gasto / max(hechas, 1):.4f} por caso)")
    return "\n".join(filas)


# --- costura PENDIENTE del M17.2 (extraer_banco) ---
# PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO.
# El script no la aplica en su sitio: eso es una decision. Ver COSTURAS.md.
# batch_nocturno.py --- justo encima de main().
import signal

PARANDO = False


def _sigterm(*_):
    global PARANDO
    PARANDO = True      # se marca aquí; se sale ENTRE tandas


signal.signal(signal.SIGTERM, _sigterm)
# y la condición del bucle de tandas pasa a ser:
#   if PARANDO or gasto_usd() - gasto_0 >= PRESUPUESTO_USD:
