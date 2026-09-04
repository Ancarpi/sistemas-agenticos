# trazas.py --- la tabla del 36.1 como código. Es la función que
# el `runtime.py` del 37.2 llevaba en línea, y su casa es esta.
import hashlib
import re

# Los siete que un run sabe de sí mismo, con los nombres del
# 36.1. Los seis primeros son OBLIGATORIOS --- el trace_id y la
# versión de la regla 7 del Anexo D ---; `model.alias` no lo es
# (un worker sin LLM no tiene), `policy.decision` es por llamada
# y no del run, y `region` la pone el despliegue, no el paquete.
OBLIGATORIOS = ("agent.id", "agent.version", "run.id",
                "thread.id", "tenant", "env")
# Los tres cubos del YAML del 36.3 repartidos entre los cinco
# peldaños del Anexo H, y leídos del `risk_tier` del `agent.yaml`
# del 32.3 --- el techo del paquete, lo único de riesgo que un
# run tiene en la mano. El peldaño de la llamada concreta vive
# por herramienta, y por eso lo lee el `guardia` y no esta
# función.
MUESTREO = {"L0": 0.02, "L1": 0.10, "L2": 0.10,
            "L3": 1.00, "L4": 1.00}
# El patrón del 4.3, literal: copiado y no importado porque
# `agente_backoffice` monta sus cinco middleware al importarse.
PERSONAL = re.compile(r"\bES\d{2}(?:[ -]?\d{4}){5}\b"
                      r"|[^@\s]+@[^@\s]+\.\w{2,}")


def atributos(pk, ctx) -> dict[str, str]:
    """El `agent.yaml` del 32.3 y el contexto del run, con los
    nombres del 36.1. Revienta por lo que falta y por lo que
    sobra, y las dos se pagan al publicar y no en la auditoría de
    dentro de seis meses. Con `.get` en los dos niveles porque la
    clave AUSENTE es el caso real, y un KeyError pelado no dice
    cuál falta."""
    a = {"agent.id": pk.get("id", ""), "run.id": ctx.get("run", ""),
         "agent.version": pk.get("version", ""),
         "thread.id": ctx.get("hilo", ""),
         "tenant": pk.get("tenant", ""), "env": ctx.get("entorno", ""),
         "model.alias": pk.get("models", {}).get("supervisor", "")}
    # `version: 4.2` en el YAML es un float, y un float no agrega
    # con la cadena «4.2» en la consulta al lake del 37.3.
    a = {k: str(v) for k, v in a.items()}
    faltan = [k for k in OBLIGATORIOS if not a[k]]
    if faltan:
        raise ValueError(f"traza sin {', '.join(faltan)}")
    sucios = sorted(k for k, v in a.items() if PERSONAL.search(v))
    if sucios:
        raise ValueError(f"dato personal en {sucios} (34.6)")
    muestrear(a, pk.get("risk_tier", ""))
    return a


def muestrear(a: dict, riesgo: str) -> bool:
    """La puerta de las evals online del 36.3, por RUN y sacada
    del `run.id` en vez de `random()`. Un run con HITL se parte en
    dos procesos por el `interrupt` del 37.2, y por span entraría
    la mitad reanudada y no la primera: el `tool_trajectory_judge`
    puntúa media trayectoria creyéndola entera. Con el hash sale
    lo mismo en los dos procesos y seis meses después. Un tier que
    no conozco se muestrea entero."""
    h = hashlib.sha256(a["run.id"].encode()).hexdigest()[:8]
    dentro = int(h, 16) / 0x1_0000_0000 < MUESTREO.get(riesgo, 1.0)
    a["eval.sampled"] = str(dentro).lower()   # viaja en la traza
    return dentro
