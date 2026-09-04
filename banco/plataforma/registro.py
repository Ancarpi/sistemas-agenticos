# registro.py --- el control plane resolviendo un id. El publicador
# deja en el volumen local el `agent.yaml` de arriba y las versiones
# aprobadas en cada entorno; un sidecar sincroniza cada 60 s.
import os
from importlib import import_module
from pathlib import Path

import yaml

import equipo                  # el validador del 30.5
import estado                  # ENTORNO, del 32.2
import identidad               # el 18.3, con su lista blanca

BUNDLES = Path(os.environ.get("BUNDLES", "/srv/banco/pkg"))
PAQUETES = {}


def cargar(agente_id: str) -> tuple[dict, object | None]:
    """Firma y retorno, los del `cargar` del 37.2: allí borras el
    `def` y pones este `import`. La caché va por `mtime` y no por
    id: sin él, la 1.5.0 no releva a la 1.4.0 en un proceso ya
    levantado, y ese es todo tu SLA de versión."""
    ruta = BUNDLES / agente_id / "agent.yaml"
    try:
        sello = ruta.stat().st_mtime_ns
    except OSError:                 # el sidecar no sincroniza
        sello = PAQUETES[agente_id][0]  # KeyError en frío: sin último bueno
    if PAQUETES.get(agente_id, (None,))[0] != sello:
        pk = yaml.safe_load(ruta.read_bytes())
        aprobadas = (ruta.parent / "aprobado").read_text().split()
        if f"{pk['version']}@{estado.ENTORNO}" not in aprobadas:
            raise PermissionError(
                f"{agente_id}: sin aprobar en {estado.ENTORNO}")
        # La puerta del 30.5, y DENTRO del `if`: un YAML leído
        # por versión y no en cada turno de cada usuario.
        # `SinDueno` hereda de PermissionError, así que la
        # recoge el mismo `except` del publicador.
        equipo.comprobar(pk)
        modulo, _, obj = pk.get("entrypoint", ":").partition(":")
        modulo = modulo.replace("/", ".").removesuffix(".py")
        fab = getattr(import_module(modulo), obj) if modulo else None
        PAQUETES[agente_id] = (sello, (pk, fab))
    pk, fab = PAQUETES[agente_id][1]
    identidad.GRAFOS.add(pk["id"])  # en TODO camino, también en el
    return pk, fab                  # acierto: el hilo() lo exige
