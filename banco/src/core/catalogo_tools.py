# src/core/catalogo_tools.py --- el catálogo del 20.4: carga los
# manifiestos del 20.1, deja fuera al que no declare su contrato y
# recorta por llamada lo que el modelo ve. Decidir es del 26.
import logging
import pathlib

import yaml

from herramientas import (buscar_transferencia, escalar_a_humano,
                          historial_cuenta, marcar_resuelta)

# Las del 20.1 con las dos que su ejercicio dejaba fuera: sin
# `approval` no hay quién apruebe un L4 ni `rollback` cómo deshacerlo.
EXIGIDAS = ("name", "version", "owner", "risk_tier", "auth",
            "effects", "idempotency", "approval", "timeouts",
            "audit", "rollback")
PELDANOS = ("L0", "L1", "L2", "L3", "L4")          # el Anexo H
# La clase de dato que `clase_y_peldano` presta al `decidir` del
# 37.2 y que el bundle del 26.2 lee en `resource.data_class`.
# Obligatoria en el manifiesto y sin valor por defecto: un
# `.get("data_class", "internal")` degrada en silencio un dato
# confidencial, que es la avería que este fichero viene a cerrar.
CLASES = ("public", "internal", "confidential", "restricted")
# El riesgo máximo que cada canal puede ofrecer: la voz del 22 se
# tapa en L1, que un dígito mal oído por el ASR no bloquee nada.
TECHO = {"voz": "L1", "email": "L2", "chat": "L3",
         "backoffice": "L4"}
IMPL = {t.name: t for t in (buscar_transferencia, historial_cuenta,
                            marcar_resuelta, escalar_a_humano)}
log = logging.getLogger("catalogo")


def _fallos(m: dict) -> list:
    """Todos los defectos, y los cuatro últimos, coherencia."""
    malos = [k for k in EXIGIDAS if not m.get(k)]
    if m.get("risk_tier") not in PELDANOS:
        malos.append("risk_tier")
    if (m.get("effects", {}).get("writes")
            and not m.get("idempotency", {}).get("key")):
        malos.append("idempotency.key")
    if (m.get("risk_tier") == "L4"
            and not m.get("approval", {}).get("allowed_approvers")):
        malos.append("approval.allowed_approvers")
    # Los dos ejes que el 20.4 cobra y que ningún valor por defecto
    # puede suplir: el nivel de identidad va en `auth` y no en
    # `preconditions`, que es prosa para el revisor, y la clase de
    # dato va escrita, porque suponerla `internal` es degradarla.
    if not isinstance(m.get("auth", {}).get("identity_level"), int):
        malos.append("auth.identity_level")
    if m.get("audit", {}).get("data_class") not in CLASES:
        malos.append("audit.data_class")
    return malos


def cargar(carpeta=pathlib.Path("tools")) -> dict:
    """Al arrancar y una sola vez, así que un YAML ilegible sube tal
    cual: aquí no hay último bueno que preservar como en el 33.6."""
    catalogo, rotos = {}, []
    for ruta in sorted(carpeta.glob("*.capability.yaml")):
        m = yaml.safe_load(ruta.read_text("utf-8")) or {}
        malos = _fallos(m)
        # El `IMPL[...]` va DETRÁS de la criba. Delante, el
        # manifiesto de una herramienta que nadie ha implementado
        # sube un KeyError pelado al importar, y quien lo lea no
        # sabrá si falta la ficha o falta la función.
        if m.get("name") not in IMPL:
            malos.append("name sin entrada en IMPL")
        if malos:
            rotos.append((ruta.name, malos))
            continue
        catalogo[m["name"]] = m | {"tool": IMPL[m["name"]]}
    sin_ficha = sorted(set(IMPL) - set(catalogo))
    if rotos or sin_ficha:
        raise RuntimeError(f"catálogo: {rotos}, sin ficha {sin_ficha}")
    return catalogo


CATALOGO = cargar()


def _cabe(m: dict, sujeto: dict, ctx: dict) -> bool:
    """Los seis ejes que el 20.4 enumera, en un solo sitio."""
    if PELDANOS.index(m["risk_tier"]) > PELDANOS.index(
            TECHO[ctx["canal"]]):
        return False
    if not set(m["auth"]["scopes"]) <= set(sujeto["scopes"]):
        return False
    if sujeto["nivel_identidad"] < m["auth"]["identity_level"]:
        return False
    for eje in ("jurisdiccion", "estado_caso", "proposito"):
        permitidos = m.get("disponibilidad", {}).get(eje)
        if permitidos and ctx.get(eje) not in permitidos:
            return False
    return m.get("coste_eur", 0.0) <= ctx["presupuesto_eur"]


def puede_ver(nombre: str, sujeto: dict, ctx: dict) -> bool:
    """La misma criba en el despacho: sacar una herramienta de
    `tools=` no la borra del historial del hilo."""
    m = CATALOGO.get(nombre)
    return m is not None and _cabe(m, sujeto, ctx)


def visibles(sujeto: dict, ctx: dict, contrato=None) -> list:
    """Lo que va a `tools=` en ESTA llamada, y el `tool_catalog` del
    `build_model_request` del 19.4, que recorta encima y no debajo."""
    ve = [n for n, m in CATALOGO.items() if _cabe(m, sujeto, ctx)]
    if contrato is not None:
        ve = [n for n in ve if n in contrato.visible_tools]
    log.info("%s ve %s de %s", sujeto["id"], ve, list(CATALOGO))
    return [CATALOGO[n]["tool"] for n in ve]


def clase_y_peldano(nombre: str) -> tuple[str, str]:
    """Las dos columnas que el `decidir` del 37.2 teclea a mano."""
    m = CATALOGO[nombre]
    return m["audit"]["data_class"], m["risk_tier"]
