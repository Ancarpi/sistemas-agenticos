#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""isa_validate --- valida un artefacto contra su esquema de schemas/.

Solo stdlib. Es el mecanismo real de las negativas de isa-eval-gate,
isa-tool-manifest, isa-context-contract e isa-scaffold-agent: la negativa
no es criterio del modelo, es este script saliendo con codigo != 0 y
diciendo QUE campo falta y DONDE.

    python3 isa_validate.py eval-card evals/sepa.yaml
    python3 isa_validate.py capability tools/*.capability.yaml
    python3 isa_validate.py agent-package catalogo/x/agent.yaml
    python3 isa_validate.py context-contract contratos/triage.yaml

Codigos de salida: 0 todos validos; 1 algun artefacto invalido;
2 error de uso o del propio validador (fichero ilegible, YAML que este
parser no entiende, palabra clave de JSON Schema sin soporte).
"""

import argparse
import datetime
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
ESQUEMAS_POR_DEFECTO = RAIZ.parents[1] / "schemas"

SUBCOMANDOS = {
    "context-contract": "context-contract.schema.json",
    "capability": "tool-capability.schema.json",
    "eval-card": "eval-card.schema.json",
    "agent-package": "agent-package.schema.json",
}


class Fallo(Exception):
    """Error del validador, no del artefacto. Sale con 2, no con 1."""


# --------------------------------------------------------------------------
# Carga: JSON, o YAML por PyYAML si esta, o por el parser minimo de abajo.
# En los tres casos los timestamps salen ya como cadenas ISO-8601.
# --------------------------------------------------------------------------

def cargar(ruta):
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as e:
        raise Fallo(f"{ruta}: no se puede leer ({e.strerror}).")
    if ruta.suffix.lower() == ".json":
        try:
            return a_iso(json.loads(texto))
        except ValueError as e:
            raise Fallo(f"{ruta}: JSON invalido ({e}).")
    try:
        import yaml
    except ImportError:
        return a_iso(yaml_minimo(texto, ruta))
    try:
        return a_iso(yaml.safe_load(texto))
    except Exception as e:  # yaml.YAMLError, sin importar el modulo
        raise Fallo(f"{ruta}: YAML invalido ({e}).")


def a_iso(dato):
    """Serializa fechas y horas a ISO-8601 antes de validar.

    `baseline: 2026-07-01` en un eval card lo devuelve yaml.safe_load
    como datetime.date, no como str, y el esquema pide "type": "string":
    sin esta conversion la propia ficha del libro falla por un error de
    tipo que no tiene nada que ver con la puerta de release.
    """
    if isinstance(dato, dict):
        return {k: a_iso(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [a_iso(v) for v in dato]
    if isinstance(dato, (datetime.datetime, datetime.date, datetime.time)):
        return dato.isoformat()
    return dato


# --------------------------------------------------------------------------
# YAML: subconjunto deliberadamente pequeno, para que el script corra sin
# dependencias. Mapas anidados por sangria, listas en bloque y en linea,
# comillas simples y dobles, comentarios. Nada mas, a proposito.
# --------------------------------------------------------------------------

CLAVE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*\s*:(\s|$)")


def yaml_minimo(texto, ruta):
    lineas = []
    for n, cruda in enumerate(texto.split("\n"), 1):
        sin = _sin_comentario(cruda.rstrip())
        if not sin.strip():
            continue
        if sin.strip() in ("---", "..."):
            continue
        lineas.append((len(sin) - len(sin.lstrip(" ")), sin.strip(), n))
    if not lineas:
        return None
    valor, i = _bloque(lineas, 0, lineas[0][0], ruta)
    if i != len(lineas):
        _sintaxis(ruta, lineas[i][2], "sangria inesperada")
    return valor


def _sintaxis(ruta, n, motivo):
    raise Fallo(f"{ruta}:{n}: YAML que este parser no entiende ({motivo}). "
                f"Instala PyYAML o simplifica el fichero.")


def _sin_comentario(linea):
    fuera, comilla = [], None
    for i, c in enumerate(linea):
        if comilla:
            fuera.append(c)
            if c == comilla:
                comilla = None
            continue
        if c in "\"'":
            comilla = c
            fuera.append(c)
            continue
        if c == "#" and (i == 0 or linea[i - 1] in " \t"):
            break
        fuera.append(c)
    return "".join(fuera)


def _bloque(lineas, i, sangria, ruta):
    if lineas[i][1].startswith("- ") or lineas[i][1] == "-":
        return _lista(lineas, i, sangria, ruta)
    return _mapa(lineas, i, sangria, ruta)


def _mapa(lineas, i, sangria, ruta):
    mapa = {}
    while i < len(lineas):
        ind, cont, n = lineas[i]
        if ind < sangria or cont.startswith("- "):
            break
        if ind > sangria:
            _sintaxis(ruta, n, "sangria inesperada")
        if not CLAVE.match(cont):
            _sintaxis(ruta, n, "se esperaba 'clave: valor'")
        clave, resto = cont.split(":", 1)
        clave, resto = clave.strip(), resto.strip()
        i += 1
        if resto:
            mapa[clave] = _escalar(resto, ruta, n)
            continue
        if i < len(lineas) and (lineas[i][0] > sangria or
                                (lineas[i][0] == sangria and
                                 lineas[i][1].startswith("- "))):
            mapa[clave], i = _bloque(lineas, i, lineas[i][0], ruta)
        else:
            mapa[clave] = None
    return mapa, i


def _lista(lineas, i, sangria, ruta):
    items = []
    while i < len(lineas):
        ind, cont, n = lineas[i]
        if ind != sangria or not (cont.startswith("- ") or cont == "-"):
            break
        cuerpo = cont[1:].strip()
        sub = [(sangria + 2, cuerpo, n)] if cuerpo else []
        j = i + 1
        while j < len(lineas) and lineas[j][0] > sangria:
            sub.append(lineas[j])
            j += 1
        if not cuerpo:
            if not sub:
                _sintaxis(ruta, n, "elemento de lista vacio")
            valor, _ = _bloque(sub, 0, sub[0][0], ruta)
        elif CLAVE.match(cuerpo):
            valor, _ = _mapa(sub, 0, sangria + 2, ruta)
        else:
            if len(sub) > 1:
                _sintaxis(ruta, n, "escalar con lineas colgando")
            valor = _escalar(cuerpo, ruta, n)
        items.append(valor)
        i = j
    return items, i


def _escalar(txt, ruta, n):
    txt = txt.strip()
    if txt[:1] == '"' and txt[-1:] == '"' and len(txt) > 1:
        return txt[1:-1].replace('\\"', '"')
    if txt[:1] == "'" and txt[-1:] == "'" and len(txt) > 1:
        return txt[1:-1].replace("''", "'")
    if txt.startswith("[") and txt.endswith("]"):
        cuerpo = txt[1:-1].strip()
        if not cuerpo:
            return []
        return [_escalar(p, ruta, n) for p in cuerpo.split(",")]
    if txt.startswith("{"):
        _sintaxis(ruta, n, "mapa en linea")
    if txt in ("true", "True"):
        return True
    if txt in ("false", "False"):
        return False
    if txt in ("null", "~"):
        return None
    try:
        return int(txt)
    except ValueError:
        pass
    try:
        return float(txt)
    except ValueError:
        return txt


# --------------------------------------------------------------------------
# JSON Schema: el subconjunto que usan los cuatro esquemas del paquete y
# nada mas. Una palabra clave que aparezca en un esquema y no este aqui es
# un fallo del validador (salida 2), nunca un artefacto que pasa sin que
# nadie lo haya comprobado.
# --------------------------------------------------------------------------

ANOTACIONES = {"$schema", "$id", "$comment", "title", "description",
               "default", "examples", "format"}

SOPORTADAS = {"type", "enum", "const", "pattern", "not", "oneOf", "allOf",
              "if", "then", "minimum", "maximum", "exclusiveMinimum",
              "minLength", "minItems", "uniqueItems", "items", "required",
              "properties", "additionalProperties", "minProperties"}

TIPOS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: (isinstance(v, (int, float))
                         and not isinstance(v, bool)),
    "boolean": lambda v: isinstance(v, bool),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
}


def nombre_tipo(valor):
    for tipo in ("null", "boolean", "integer", "number", "string", "array",
                 "object"):
        if TIPOS[tipo](valor):
            return tipo
    return type(valor).__name__


def muestra(valor):
    if isinstance(valor, str):
        corto = valor if len(valor) <= 40 else valor[:37] + "..."
        return f"'{corto}'"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if valor is None:
        return "null"
    if isinstance(valor, (dict, list)):
        return nombre_tipo(valor)
    return str(valor)


def validar(dato, esquema, ruta, errores, condicion=None):
    """Acumula en `errores` un mensaje por defecto, con su ruta."""
    for clave in esquema:
        if clave not in SOPORTADAS and clave not in ANOTACIONES:
            raise Fallo(f"palabra clave de JSON Schema sin soporte: "
                        f"'{clave}' en {ruta or '(raiz)'}. Anadela a "
                        f"isa_validate.py antes de confiar en la validacion.")

    def err(texto):
        cola = f" (exigido cuando {condicion})" if condicion else ""
        errores.append(f"{ruta or '(raiz)'}: {texto}{cola}")

    if "type" in esquema:
        tipos = esquema["type"]
        tipos = tipos if isinstance(tipos, list) else [tipos]
        if not any(TIPOS[t](dato) for t in tipos):
            err(f"se esperaba {' o '.join(tipos)}, hay "
                f"{nombre_tipo(dato)} {muestra(dato)}")
            return
    if "enum" in esquema and dato not in esquema["enum"]:
        err(f"{muestra(dato)} no esta en el enum "
            f"({', '.join(str(v) for v in esquema['enum'])})")
    if "const" in esquema and dato != esquema["const"]:
        err(f"{muestra(dato)} deberia ser {muestra(esquema['const'])}")
    if "pattern" in esquema and isinstance(dato, str):
        if not re.search(esquema["pattern"], dato):
            err(f"{muestra(dato)} no cumple el patron {esquema['pattern']}")
    if "not" in esquema and cumple(dato, esquema["not"], ruta):
        prohibido = esquema["not"]
        if list(prohibido) == ["pattern"]:
            err(f"{muestra(dato)} coincide con el patron prohibido "
                f"{prohibido['pattern']}")
        else:
            err(f"{muestra(dato)} coincide con lo que el esquema prohibe")
    if "oneOf" in esquema:
        motivos = []
        validas = 0
        for alternativa in esquema["oneOf"]:
            parciales = []
            validar(dato, alternativa, ruta, parciales)
            if parciales:
                motivos.append(parciales[0].split(": ", 1)[-1])
            else:
                validas += 1
        if validas != 1:
            err(f"{muestra(dato)} no cumple ninguna alternativa: "
                + " | ".join(motivos))
    for numero in ("minimum", "maximum", "exclusiveMinimum"):
        if numero in esquema and TIPOS["number"](dato):
            limite = esquema[numero]
            malo = (numero == "minimum" and dato < limite or
                    numero == "maximum" and dato > limite or
                    numero == "exclusiveMinimum" and dato <= limite)
            if malo:
                signo = {"minimum": ">=", "maximum": "<=",
                         "exclusiveMinimum": ">"}[numero]
                err(f"{muestra(dato)} incumple {signo} {limite}")
    if "minLength" in esquema and isinstance(dato, str):
        if len(dato) < esquema["minLength"]:
            err(f"vacio o mas corto de {esquema['minLength']} caracteres")
    if isinstance(dato, list):
        if "minItems" in esquema and len(dato) < esquema["minItems"]:
            err(f"la lista tiene {len(dato)} elementos y el esquema pide "
                f"minItems {esquema['minItems']}")
        if esquema.get("uniqueItems"):
            vistos, repetidos = [], []
            for elemento in dato:
                if elemento in vistos and elemento not in repetidos:
                    repetidos.append(elemento)
                vistos.append(elemento)
            if repetidos:
                err("hay elementos repetidos: "
                    + ", ".join(muestra(r) for r in repetidos))
        if "items" in esquema:
            for indice, elemento in enumerate(dato):
                validar(elemento, esquema["items"],
                        hijo(ruta, indice), errores, condicion)
    if isinstance(dato, dict):
        for obligatorio in esquema.get("required", []):
            if obligatorio not in dato or dato[obligatorio] is None:
                err(f"falta {obligatorio}")
        if "minProperties" in esquema:
            if len(dato) < esquema["minProperties"]:
                err(f"declara {len(dato)} campos y el esquema pide al "
                    f"menos {esquema['minProperties']}")
        propiedades = esquema.get("properties", {})
        for clave, valor in dato.items():
            if clave in propiedades:
                validar(valor, propiedades[clave], hijo(ruta, clave),
                        errores, condicion)
            elif "additionalProperties" in esquema:
                extra = esquema["additionalProperties"]
                if extra is False:
                    errores.append(f"{hijo(ruta, clave)}: campo desconocido "
                                   f"(el esquema no admite mas campos aqui)")
                elif isinstance(extra, dict):
                    validar(valor, extra, hijo(ruta, clave), errores,
                            condicion)
    for sub in esquema.get("allOf", []):
        validar(dato, sub, ruta, errores, condicion)
    if "if" in esquema:
        if cumple(dato, esquema["if"], ruta) and "then" in esquema:
            validar(dato, esquema["then"], ruta, errores,
                    condicion or describe_condicion(esquema["if"], dato))


def hijo(ruta, clave):
    return f"{ruta}/{clave}" if ruta else str(clave)


def cumple(dato, esquema, ruta):
    parciales = []
    validar(dato, esquema, ruta, parciales)
    return not parciales


def describe_condicion(condicion, dato):
    """`risk_tier = irreversible_high`, para que el mensaje diga por que."""
    partes = []
    if isinstance(dato, dict):
        for clave in condicion.get("properties", {}):
            if clave in dato:
                partes.append(f"{clave} = {muestra(dato[clave])}")
    return ", ".join(partes) or "se cumple la condicion del esquema"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def leer_esquema(directorio, fichero):
    ruta = pathlib.Path(directorio) / fichero
    if not ruta.is_file():
        raise Fallo(f"no encuentro el esquema {ruta}. Usa --esquemas DIR.")
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError as e:
        raise Fallo(f"{ruta}: JSON invalido ({e}).")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Valida artefactos del paquete contra schemas/.",
        epilog="Salida: 0 validos, 1 algun invalido, 2 error de uso.")
    ap.add_argument("subcomando", choices=sorted(SUBCOMANDOS),
                    metavar="{" + ",".join(sorted(SUBCOMANDOS)) + "}")
    ap.add_argument("rutas", nargs="+", type=pathlib.Path,
                    help="uno o mas ficheros YAML o JSON")
    ap.add_argument("--esquemas", default=ESQUEMAS_POR_DEFECTO,
                    help="directorio schemas/ (por defecto, el del paquete)")
    ap.add_argument("-q", "--silencioso", action="store_true",
                    help="no imprime los OK, solo los errores")
    args = ap.parse_args(argv)

    nombre_esquema = SUBCOMANDOS[args.subcomando]
    try:
        esquema = leer_esquema(args.esquemas, nombre_esquema)
    except Fallo as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    invalidos = 0
    for ruta in args.rutas:
        try:
            dato = cargar(ruta)
            if not isinstance(dato, dict):
                print(f"ERROR: {ruta}: se esperaba un mapa en la raiz, hay "
                      f"{nombre_tipo(dato)}.", file=sys.stderr)
                return 2
            errores = []
            validar(dato, esquema, "", errores)
        except Fallo as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        if errores:
            invalidos += 1
            print(f"INVALIDO {ruta}  [{nombre_esquema}]")
            for mensaje in errores:
                print(f"  {mensaje}")
        elif not args.silencioso:
            print(f"OK {ruta}  [{nombre_esquema}]")

    if len(args.rutas) > 1 and (invalidos or not args.silencioso):
        validos = len(args.rutas) - invalidos
        sys.stdout.flush()
        print(f"{validos} valido{'' if validos == 1 else 's'}, "
              f"{invalidos} invalido{'' if invalidos == 1 else 's'}.",
              file=sys.stderr if invalidos else sys.stdout)
    return 1 if invalidos else 0


if __name__ == "__main__":
    sys.exit(main())
