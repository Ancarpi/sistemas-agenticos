# src/core/router.py --- el router del 19.2, ya ejecutable: lee
# config/model_routing.yaml y devuelve el modelo de cada nodo con
# su presupuesto de pensamiento, su tope de coste y su degradado.
import os
import random
import re
import time

import yaml

from src.core.models import get_model      # la fábrica del 0.4

FICHERO = os.getenv("MODEL_ROUTING", "config/model_routing.yaml")
ALIAS = re.compile(r"^[a-z][a-z0-9-]{2,39}$")  # sin '/': sin vendor
PARAMS = ("temperature", "reasoning_effort", "max_output_tokens")
UMBRAL = 3      # fallos seguidos antes de abrir el disyuntor
PAUSA = 60.0    # s que un alias caído queda fuera del reparto

PRECIOS: dict[str, tuple[float, float]] = {}   # alias -> EUR/1M
_FALLOS: dict[str, int] = {}
_ABIERTO: dict[str, float] = {}


class RutaImposible(RuntimeError):
    """Fallo de política, no del modelo."""


def cargar(fichero: str = FICHERO) -> dict[str, dict]:
    with open(fichero, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    PRECIOS.update({a: tuple(p) for a, p in doc["precios"].items()})
    rutas = {}
    for nodo, r in doc["routes"].items():
        for alias in (r["primary"], r["fallback"]):
            # La regla del 19.2, cobrada: un id de proveedor trae
            # la barra del namespace y no pasa el patrón.
            if not ALIAS.match(alias) or alias not in PRECIOS:
                raise ValueError(f"{nodo}: '{alias}' no es un alias"
                                 " del gateway con precio")
        rutas[nodo] = dict(r, params={k: r[k] for k in PARAMS
                                      if k in r})
    return rutas


RUTAS = cargar()   # al importar: un alias mal escrito revienta
                   # el arranque, y no el nodo de las 03:12


def anotar(alias: str, ok: bool) -> None:
    """Sin disyuntor, degradar cuesta la espera del alias caído en
    CADA llamada."""
    if ok:
        _FALLOS.pop(alias, None)
        _ABIERTO.pop(alias, None)
        return
    _FALLOS[alias] = _FALLOS.get(alias, 0) + 1
    if _FALLOS[alias] >= UMBRAL:
        _ABIERTO[alias] = time.monotonic() + PAUSA


def cadena(nodo: str) -> list[str]:
    r = RUTAS[nodo]
    orden = [r["primary"], r["fallback"]]
    if random.randrange(100) < r.get("canary", 0):
        orden.reverse()               # el 90/10 del Ejercicio 19.2
    if not r.get("degradar", True):
        orden = orden[:1]   # un intento: esta ruta prefiere fallar
    ahora = time.monotonic()
    vivos = [a for a in orden if _ABIERTO.get(a, 0.0) <= ahora]
    if not vivos:
        raise RutaImposible(f"{nodo}: sin alias autorizado vivo")
    return vivos


def invocar(nodo: str, mensajes: list, **extra):
    """Devuelve (respuesta, alias). El alias sale para la traza:
    con canary encendido no se deduce de la configuración."""
    r, ultimo = RUTAS[nodo], None
    for alias in cadena(nodo):
        try:
            respuesta = get_model(
                alias, **{**r["params"], **extra}).invoke(mensajes)
        except Exception as e:    # el gateway del 0.5 ya reintentó
            anotar(alias, False)
            ultimo = e
            continue
        anotar(alias, True)
        return respuesta, alias
    raise RutaImposible(f"{nodo}: cadena agotada") from ultimo


def presupuesto_entrada(nodo, alias, contrato=None) -> int:
    """Traduce el tope de coste a tokens de ENTRADA, la mitad que
    tú controlas: la salida se reserva ENTERA a su precio."""
    r, (p_entrada, p_salida) = RUTAS[nodo], PRECIOS[alias]
    resto = (r["max_cost_eur"]
             - r["params"]["max_output_tokens"] * p_salida / 1e6)
    if resto <= 0:
        raise RutaImposible(f"{nodo}: la salida agota el tope")
    tope = int(resto * 1e6 / p_entrada)
    # Manda el más estricto: la ruta habla de una clase de nodos y
    # el contrato del 19.1 habla de este nodo.
    return min(tope, contrato.max_input_tokens) if contrato else tope


def recortar(mensajes: list, contrato, tope: int, contar=None):
    """El «context rot» del 19.3, medido: deja lo que cabe en
    `tope` tokens sin tocar lo que el contrato declara
    imprescindible, y da el parte para la traza del 24.2."""
    contar = contar or (lambda m: len(str(m.content)) // 4 + 8)
    bloq: list[list] = []
    for m in mensajes:
        if m.type == "tool" and bloq and getattr(
                bloq[-1][0], "tool_calls", None):
            bloq[-1].append(m)        # el par NUNCA se parte
        else:
            bloq.append([m])
    gasto, quedan, lleno = 0, [], False
    for i, b in reversed(list(enumerate(bloq))):
        fijo = (b[0].type == "system" or b[0].additional_kwargs
                .get("clave") in contrato.allowed_state_keys)
        coste = sum(contar(m) for m in b)
        if not fijo and (lleno or gasto + coste > tope):
            lleno = True    # se corta por lo VIEJO, no por lo caro
            continue
        gasto += coste
        quedan.append(i)
    if gasto > tope:        # ni lo imprescindible cabe; no se
        raise RutaImposible(   # recorta, se rediseña el contrato
            f"{contrato.node}: lo fijo pide {gasto} de {tope}")
    parte = {"nodo": contrato.node, "tokens": gasto, "tope": tope,
             "fuera": len(bloq) - len(quedan)}
    return [m for i in sorted(quedan) for m in bloq[i]], parte
