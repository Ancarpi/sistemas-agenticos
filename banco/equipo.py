# equipo.py --- el validador de `equipo.yaml`. Dos funciones: si
# un paquete puede publicarse, y a quién se despierta. Lo importa
# el `registro.py` del 32.3, y el publicador de CI también.
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

RUTA = Path(os.environ.get("EQUIPO", "/srv/banco/equipo.yaml"))
PELDANOS = ("L0", "L1", "L2", "L3", "L4")   # el Anexo H, en orden
FIRMAS = ("owner_tecnico", "sube_autonomia", "firmado_hasta",
          "firmado_el")
CADUCA = timedelta(days=180)   # vigencia de la firma de riesgo


class SinDueno(PermissionError):
    """Hereda de PermissionError para que el `except` del
    publicador sea el que ya recoge el «sin aprobar aquí» del
    32.3."""


def leer() -> dict:
    """Sin caché: esto se lee al publicar y al refrescar un
    paquete, nunca por turno. El día que sea por turno, la caché
    va por `mtime` como la del registro."""
    return yaml.safe_load(RUTA.read_bytes())


def comprobar(pk: dict, publicando: bool = False) -> dict:
    """Las reglas duras sobre el `agent.yaml` del 32.3. Devuelve
    la ficha del equipo para quien quiera pintarla."""
    eq = leer()
    ficha = eq["agentes"].get(pk["id"])
    if ficha is None:
        raise SinDueno(f"{pk['id']}: no figura en equipo.yaml")
    rie = ficha.get("owner_riesgo")
    if not rie:                    # la regla de este apartado
        raise SinDueno(f"{pk['id']}: sin owner de riesgo")
    faltan = [c for c in FIRMAS if not ficha.get(c)]
    if faltan:
        raise SinDueno(f"{pk['id']}: ficha sin {', '.join(faltan)}")
    tec = ficha["owner_tecnico"]
    if tec == rie:
        raise SinDueno(f"{pk['id']}: {tec} se firmaría a sí mismo")
    fuera = [q for q in (tec, rie) if q not in eq["personas"]]
    if fuera:
        raise SinDueno(f"{pk['id']}: {fuera} ya no está en la casa")
    # El techo lo declara el paquete y la firma la declara riesgo:
    # dos ficheros, dos pull requests y dos revisores distintos.
    techo, firma = str(pk.get("risk_tier", "")), \
        str(ficha["firmado_hasta"])
    if techo not in PELDANOS or firma not in PELDANOS:
        raise SinDueno(f"{pk['id']}: peldaño {techo!r}/{firma!r}")
    if PELDANOS.index(techo) > PELDANOS.index(firma):
        raise SinDueno(f"{pk['id']}: declara {techo} sobre {firma}"
                       f" firmado; lo sube {ficha['sube_autonomia']}")
    # La caducidad solo se cobra al publicar. Ver la trampa: en
    # `cargar` tumbaría de madrugada lo que lleva meses sirviendo.
    vence = date.fromisoformat(str(ficha["firmado_el"])) + CADUCA
    if publicando and vence < date.today():
        raise SinDueno(f"{pk['id']}: la firma de {rie} venció el"
                       f" {vence}; toca revisión antes de publicar")
    return ficha


def de_turno(cuando: datetime | None = None) -> tuple[str, str]:
    """Quien coge el aviso y a quién salta a los `ack_minutos`. El
    turno se cuenta en UTC desde `arranque`, porque una tabla de
    tramos en hora local deja la noche del cambio de hora con dos
    personas de guardia en octubre y con ninguna en marzo."""
    t = leer()["turnos"]
    ahora = cuando or datetime.now(timezone.utc)
    n = (ahora - datetime.fromisoformat(t["arranque"])) \
        // timedelta(hours=t["turno_horas"])
    return t["rotacion"][n % len(t["rotacion"])], t["jefe"]


def a_quien_despierto(agente_id: str) -> dict:
    """La respuesta de las tres de la mañana: entra el `agent.id`
    que la alerta del 36.2 ya trae y sale el aviso con nombres.
    Un id que no figura sale con `?` en vez de reventar."""
    eq = leer()
    ficha = eq["agentes"].get(agente_id, {})
    persona, jefe = de_turno()
    aviso = {"de_turno": persona, "jefe": jefe,
             "busca": eq["personas"][persona]["busca"]}
    for c in ("owner_tecnico", "owner_riesgo", "sube_autonomia"):
        aviso[c] = ficha.get(c, "?")
    return aviso
