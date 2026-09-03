#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extraer_banco --- reconstruye banco/ desde libro.md.

Solo stdlib. El mapeo vive una vez y como datos, en mapeo.yaml; este script
lo aplica. Si un rango de lineas ya no empieza y acaba donde decia, FALLA:
el libro sigue vivo, asi que la extraccion tiene que romperse en voz alta en
vez de escribir basura.

    python3 extraer_banco.py --libro ../../../fuente/libro.md
    python3 extraer_banco.py --verificar        # no escribe nada
    python3 extraer_banco.py --resincronizar    # reubica por ancla

Codigos de salida: 0 todo bien; 1 anclas desplazadas o mapeo invalido.
"""

import argparse
import pathlib
import re
import unicodedata
import sys

RAIZ = pathlib.Path(__file__).resolve().parent
LIBRO_POR_DEFECTO = RAIZ.parents[2] / "fuente" / "libro.md"
DESTINO_POR_DEFECTO = RAIZ.parents[1] / "banco"


def loc(modulo):
    """M21.4 para un modulo; `Ej. 0.1` se cita tal cual."""
    return ("M" + modulo) if modulo[:1].isdigit() else modulo


COMENTARIO = {".py": "#", ".sql": "--", ".yaml": "#", ".yml": "#",
              ".json": None, ".toml": "#", ".md": None, ".ini": "#",
              ".example": "#", ".sh": "#"}


# --------------------------------------------------------------------------
# mapeo.yaml: subconjunto de YAML deliberadamente pequeno (sin dependencias)
# --------------------------------------------------------------------------

def _escalar(txt):
    txt = txt.strip()
    if txt.startswith("[") and txt.endswith("]"):
        cuerpo = txt[1:-1].strip()
        return _lista(cuerpo) if cuerpo else []
    if txt.startswith("'"):
        return txt[1:txt.rindex("'")].replace("''", "'")
    return txt


def _lista(cuerpo):
    piezas, actual, entre_comillas = [], "", False
    i = 0
    while i < len(cuerpo):
        c = cuerpo[i]
        if c == "'":
            if entre_comillas and i + 1 < len(cuerpo) and cuerpo[i + 1] == "'":
                actual += "''"
                i += 2
                continue
            entre_comillas = not entre_comillas
        if c == "," and not entre_comillas:
            piezas.append(actual)
            actual = ""
        else:
            actual += c
        i += 1
    piezas.append(actual)
    return [_escalar(p) for p in piezas]


def leer_mapeo(ruta):
    """Lee mapeo.yaml. Formato: escalares de primer nivel y una lista de
    mappings de dos espacios bajo `entradas:`. Nada mas, a proposito."""
    cabecera, entradas, actual = {}, [], None
    for n, cruda in enumerate(ruta.read_text(encoding="utf-8").split("\n"), 1):
        linea = "" if cruda.lstrip().startswith("#") else cruda.rstrip()
        if not linea.strip():
            continue
        if linea.startswith("  - "):
            actual = {}
            entradas.append(actual)
            clave, _, valor = linea[4:].partition(":")
            actual[clave.strip()] = _escalar(valor)
        elif linea.startswith("    ") and actual is not None:
            clave, _, valor = linea.strip().partition(":")
            actual[clave.strip()] = _escalar(valor)
        elif linea.rstrip().endswith(":"):
            continue                      # `entradas:`
        elif not linea.startswith(" "):
            clave, _, valor = linea.partition(":")
            cabecera[clave.strip()] = _escalar(valor)
        else:
            raise SystemExit(f"mapeo.yaml:{n}: no entiendo esta linea: {cruda!r}")
    return cabecera, entradas


def rangos(entrada):
    salida = []
    for texto in entrada.get("bloques", []):
        ini, _, fin = str(texto).partition("-")
        salida.append((int(ini), int(fin)))
    return salida


# --------------------------------------------------------------------------
# verificacion de anclas
# --------------------------------------------------------------------------

def plano(texto):
    """La forma en que se comparan las anclas: sin tildes y con los espacios
    colapsados. Una tilde anadida a un comentario del codigo no es que el libro
    se haya movido, y comparando byte a byte lo parecia --- una pasada de
    correccion ortografica invalidaba cincuenta anclas de golpe."""
    sin = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin).strip()


def comprobar(lineas, entrada):
    """Devuelve la lista de desajustes (vacia si el mapeo sigue vigente)."""
    fallos = []
    anclas = entrada.get("anclas", [])
    finales = entrada.get("anclas_fin", [])
    for i, (ini, fin) in enumerate(rangos(entrada)):
        for numero, esperada, extremo in ((ini, anclas[i], "inicio"),
                                          (fin, finales[i], "fin")):
            real = lineas[numero - 1].strip() if 0 < numero <= len(lineas) else "<fuera del fichero>"
            if plano(real) != plano(esperada):
                fallos.append(
                    f"{entrada['destino']} ({loc(entrada['modulo'])}) bloque {ini}-{fin}: "
                    f"el {extremo} deberia ser {esperada!r} y la linea {numero} dice {real!r}")
    return fallos


def reubicar(lineas, ancla, ancla_fin, cerca_de, largo):
    """Busca el par de anclas que mejor explica el bloque que se movio.

    Ni la primera ni la ultima linea de un bloque son unicas en el libro --- hay
    once bloques que empiezan por `from typing import Literal` ---, asi que se
    puntua cada par candidato: primero el que conserva el numero de lineas,
    despues el que cae mas cerca de donde estaba. Sin lo primero, un bloque se
    recorta contra la siguiente aparicion de su ancla de cierre."""
    mejor = None
    techo = max(largo * 3, largo + 60)
    for i in range(1, len(lineas) + 1):
        if plano(lineas[i - 1]) != plano(ancla):
            continue
        for j in range(i, min(i + techo, len(lineas)) + 1):
            if plano(lineas[j - 1]) != plano(ancla_fin):
                continue
            coste = (abs((j - i) - largo), abs(i - cerca_de))
            if mejor is None or coste < mejor[0]:
                mejor = (coste, (i, j))
    return mejor[1] if mejor else None


# --------------------------------------------------------------------------
# escritura
# --------------------------------------------------------------------------

def texto(lineas, ini, fin):
    return "\n".join(lineas[ini - 1:fin])


def marcador(destino, modulo, nota, pendiente):
    prefijo = COMENTARIO.get(pathlib.Path(destino).suffix, "#")
    if prefijo is None:
        return None
    cabecera = (f"costura PENDIENTE del {loc(modulo)}" if pendiente
                else f"anadido del {loc(modulo)}")
    linea = (f"\n{prefijo} El script no la aplica en su sitio: eso es una "
             f"decision. Ver COSTURAS.md.\n" if pendiente else "")
    return (f"\n\n{prefijo} --- {cabecera} (extraer_banco) ---\n"
            f"{prefijo} {nota}{linea or chr(10)}")


def aplicar(entradas, lineas, destino_raiz, escribir):
    escritos, costuras = {}, []
    for entrada in entradas:
        destino = entrada["destino"]
        modo = entrada["modo"]
        if modo == "fragmento":
            for ini, fin in rangos(entrada):
                costuras.append((entrada, texto(lineas, ini, fin)))
            continue
        if modo == "plantilla":
            cuerpo = (RAIZ / "plantillas" / entrada["plantilla"]).read_text(encoding="utf-8")
        else:
            cuerpo = "\n".join(texto(lineas, ini, fin) for ini, fin in rangos(entrada))
            if not cuerpo.endswith("\n"):
                cuerpo += "\n"
        if modo == "patch":
            if destino not in escritos:
                raise SystemExit(f"{destino}: un patch antes de su fichero base")
            marca = marcador(destino, entrada["modulo"], entrada["nota"],
                             entrada.get("pendiente") == "si")
            escritos[destino] += (marca + cuerpo) if marca else cuerpo
            costuras.append((entrada, None))
        else:
            if destino in escritos:
                raise SystemExit(f"{destino}: dos entradas verbatim para el mismo destino")
            escritos[destino] = cuerpo
    if escribir:
        for destino, cuerpo in escritos.items():
            ruta = destino_raiz / destino
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(cuerpo, encoding="utf-8")
    return escritos, costuras


def mapeo_md(cabecera, entradas, escritos):
    filas = []
    for entrada in entradas:
        if entrada["modo"] == "fragmento":
            continue
        rango = ", ".join("L%d-%d" % r for r in rangos(entrada)) or "---"
        filas.append((entrada["destino"], loc(entrada["modulo"]),
                      entrada["modo"], rango, entrada["nota"]))
    salida = [
        "# MAPEO --- que modulo del libro entrega cada fichero",
        "",
        "**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**",
        "se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.",
        "",
        f"Libro de origen: {cabecera.get('libro_lineas')} lineas. "
        f"{len(escritos)} ficheros, {len(filas)} entradas de mapeo.",
        "",
        "| Fichero | Modulo | Modo | Lineas del libro | Nota |",
        "|---|---|---|---|---|",
    ]
    for destino, modulo, modo, rango, nota in filas:
        salida.append(f"| `{destino}` | {modulo} | {modo} | {rango} | {nota} |")
    salida += [
        "",
        "`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del",
        "fichero, con un marcador que nombra su modulo; las que ademas exigen una",
        "decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el",
        "paquete, no codigo del libro.",
        "",
    ]
    return "\n".join(salida)


def costuras_md(costuras):
    salida = [
        "# COSTURAS --- lo que el libro deja para aplicar a mano",
        "",
        "**Generado por `tools/extraer_banco/extraer_banco.py`.**",
        "",
        "Un bloque del libro que parchea otro fichero se extrae **al final** del",
        "fichero destino, con un marcador que nombra su modulo. Cuando el orden",
        "no importa, ese anadido ya es el estado final. Cuando si importa, el",
        "script **no** intenta fusionarlo: pegarlo en su sitio es una decision, no",
        "una operacion de texto. Estas son las que quedan pendientes.",
        "",
        "| Destino | Modulo | Que hay que hacer |",
        "|---|---|---|",
    ]
    pendientes = 0
    for entrada, _ in costuras:
        if entrada["modo"] != "patch" or entrada.get("pendiente") != "si":
            continue
        pendientes += 1
        salida.append(f"| `{entrada['destino']}` | {loc(entrada['modulo'])} | {entrada['nota']} |")
    if not pendientes:
        salida.append("| --- | --- | Ninguna. |")
    salida += ["",
               "El resto de los `patch` de `MAPEO.md` son anadidos al final que no",
               "piden nada mas: el fichero ya queda como tiene que quedar.",
               ""]
    for entrada, cuerpo in costuras:
        if cuerpo is None:
            continue
        salida += [f"## Costura del {loc(entrada['modulo'])}", "",
                   entrada["nota"], "", "``` python", cuerpo, "```", ""]
    return "\n".join(salida)


# --------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--libro", type=pathlib.Path, default=LIBRO_POR_DEFECTO)
    p.add_argument("--destino", type=pathlib.Path, default=DESTINO_POR_DEFECTO)
    p.add_argument("--mapeo", type=pathlib.Path, default=RAIZ / "mapeo.yaml")
    p.add_argument("--verificar", action="store_true",
                   help="comprueba las anclas y no escribe nada")
    p.add_argument("--resincronizar", action="store_true",
                   help="reubica los rangos por ancla y reescribe mapeo.yaml")
    args = p.parse_args(argv)

    if not args.libro.exists():
        print(f"ERROR: no encuentro el libro en {args.libro}", file=sys.stderr)
        return 1
    lineas = args.libro.read_text(encoding="utf-8").split("\n")
    cabecera, entradas = leer_mapeo(args.mapeo)

    esperadas = cabecera.get("libro_lineas")
    if esperadas and int(esperadas) != len(lineas):
        print(f"AVISO: el libro tiene {len(lineas)} lineas y mapeo.yaml anoto "
              f"{esperadas}. Las anclas dicen si el mapeo sigue valido.",
              file=sys.stderr)

    fallos = [f for entrada in entradas for f in comprobar(lineas, entrada)]

    if args.resincronizar:
        return resincronizar(args, lineas, entradas, fallos)

    if fallos:
        print("EL LIBRO SE HA MOVIDO. No escribo nada.", file=sys.stderr)
        for f in fallos:
            print("  - " + f, file=sys.stderr)
        print("\nRevisa mapeo.yaml, o prueba --resincronizar y VERIFICA el diff.",
              file=sys.stderr)
        return 1

    escritos, costuras = aplicar(entradas, lineas, args.destino,
                                 escribir=not args.verificar)
    if args.verificar:
        print(f"OK: {len(entradas)} entradas, {len(escritos)} ficheros, anclas al dia.")
        return 0

    (args.destino / "MAPEO.md").write_text(
        mapeo_md(cabecera, entradas, escritos), encoding="utf-8")
    (args.destino / "COSTURAS.md").write_text(costuras_md(costuras), encoding="utf-8")
    print(f"OK: {len(escritos)} ficheros escritos en {args.destino}")
    print("     mas MAPEO.md y COSTURAS.md")
    return 0


def resincronizar(args, lineas, entradas, fallos):
    if not fallos:
        print("Nada que resincronizar: las anclas estan al dia.")
        return 0
    crudo = args.mapeo.read_text(encoding="utf-8")
    cambios = 0
    for entrada in entradas:
        viejos = rangos(entrada)
        if not viejos or not comprobar(lineas, entrada):
            continue
        nuevos = []
        for i, (ini, fin) in enumerate(viejos):
            par = reubicar(lineas, entrada["anclas"][i],
                           entrada["anclas_fin"][i], ini, fin - ini)
            if par is None:
                print(f"ERROR: no encuentro las anclas de {entrada['destino']} "
                      f"({loc(entrada['modulo'])}, bloque {ini}-{fin}). "
                      f"Ese bloque hay que remapearlo a mano.", file=sys.stderr)
                return 1
            if (par[1] - par[0]) != (fin - ini):
                print(f"  AVISO: {entrada['destino']} ({loc(entrada['modulo'])}) pasa de "
                      f"{fin - ini + 1} a {par[1] - par[0] + 1} lineas: el bloque no "
                      f"solo se movio, cambio. Lee el diff del libro.", file=sys.stderr)
            nuevos.append(par)
        if nuevos != viejos:
            antes = "bloques: [%s]" % ", ".join("%d-%d" % r for r in viejos)
            ahora = "bloques: [%s]" % ", ".join("%d-%d" % r for r in nuevos)
            if crudo.count(antes) != 1:
                print(f"ERROR: '{antes}' no es unico en mapeo.yaml; "
                      f"resincroniza a mano.", file=sys.stderr)
                return 1
            crudo = crudo.replace(antes, ahora)
            cambios += 1
            print(f"  {entrada['destino']}: {antes} -> {ahora}")
    crudo = _sustituir_cabecera(crudo, len(lineas))
    args.mapeo.write_text(crudo, encoding="utf-8")
    print(f"mapeo.yaml resincronizado: {cambios} entradas. REVISA EL DIFF "
          f"antes de commitear y vuelve a ejecutar sin --resincronizar.")
    return 0


def _sustituir_cabecera(crudo, total):
    salida = []
    for linea in crudo.split("\n"):
        if linea.startswith("libro_lineas:"):
            salida.append(f"libro_lineas: {total}")
        else:
            salida.append(linea)
    return "\n".join(salida)


if __name__ == "__main__":
    sys.exit(main())
