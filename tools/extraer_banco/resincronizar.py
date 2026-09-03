#!/usr/bin/env python3
"""resincronizar --- reubica los rangos de mapeo.yaml cuando el libro se mueve.

POR QUE NO BASTA EL --resincronizar DEL EXTRACTOR. Aquel busca cerca de donde
estaba el bloque, lo que resuelve una deriva de decenas de lineas pero no una de
ochocientas. Y compara las anclas byte a byte, asi que una pasada de correccion
ortografica sobre los comentarios del codigo invalida cincuenta anclas de golpe.

COMO BUSCA ESTE, y por que en ese orden. Cada entrada declara su `modulo`, asi
que su bloque solo puede estar dentro de la seccion de ese modulo: buscar en todo
el libro es lo que hace que un ancla generica --- `@tool`, `from pydantic import
BaseModel`, `class Informe(BaseModel):` --- case en el sitio equivocado y la
extraccion escriba prosa dentro de un `.py`. El indice de secciones se construye
FUERA de las vallas de codigo, porque dentro hay comentarios como
`# 12.5 servidor.py ---` que pasan por titulares.

LA COMPROBACION QUE MANDA no es que las anclas casen: es que el arbol extraido
compile. Un ancla generica puede casar en el sitio equivocado y dejar el mapeo
"al dia" mientras el .py contiene un parrafo del libro.

    python3 resincronizar.py --libro ../../fuente/libro.md [--escribir]
"""
import argparse
import pathlib
import re
import sys
import unicodedata

import yaml


def plano(texto):
    sin = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin).strip()


def secciones(lineas):
    """clave de seccion -> (primera linea, ultima), ignorando las vallas."""
    marcas, dentro = [], False
    for i, l in enumerate(lineas):
        if l.startswith("```"):
            dentro = not dentro
            continue
        if dentro:
            continue
        m = re.match(r"^#{1,2} (?:Módulo )?(\d+)(?:\.(\d+))?\b", l)
        if m:
            marcas.append((i + 1, m.group(1) + ("." + m.group(2) if m.group(2) else "")))
        a = re.match(r"^# Anexo ([A-J])", l)
        if a:
            marcas.append((i + 1, "A·" + a.group(1)))
    out = {}
    for k, (ln, clave) in enumerate(marcas):
        fin = marcas[k + 1][0] - 1 if k + 1 < len(marcas) else len(lineas)
        out.setdefault(clave, (ln, fin))
    return out


def rango_de(modulo, sec, total):
    mod = str(modulo).replace("Ej. ", "").strip()
    if mod in sec:
        return sec[mod]
    return sec.get(mod.split(".")[0], (1, total))


def busca(pl_lineas, txt, lo, hi, desde):
    t = plano(txt)
    if not t:
        return None
    ini = max(lo - 1, desde)
    for exacto in (True, False):
        for i in range(ini, min(hi, len(pl_lineas))):
            if pl_lineas[i] == t or (not exacto and pl_lineas[i].startswith(t)):
                return i + 1
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--libro", required=True)
    ap.add_argument("--mapeo", default=str(pathlib.Path(__file__).parent / "mapeo.yaml"))
    ap.add_argument("--escribir", action="store_true",
                    help="sin esto solo informa; el diff se revisa antes de escribir")
    a = ap.parse_args()

    lineas = pathlib.Path(a.libro).read_text(encoding="utf-8").split("\n")
    pl_lineas = [plano(l) for l in lineas]
    sec = secciones(lineas)
    mapa = pathlib.Path(a.mapeo)
    m = yaml.safe_load(mapa.read_text(encoding="utf-8"))

    cambios, fallos = [], []
    for e in m["entradas"]:
        if e.get("modo") == "plantilla" or "bloques" not in e:
            continue
        lo, hi = rango_de(e.get("modulo", ""), sec, len(lineas))
        hi = min(hi + 40, len(lineas))
        ia, fa = e.get("anclas") or [], e.get("anclas_fin") or []
        nuevos, cur = [], lo - 1
        for k, r in enumerate(e["bloques"]):
            ai = ia[k] if k < len(ia) else None
            bi = fa[k] if k < len(fa) else None
            if not ai or not bi:
                nuevos.append(str(r))
                continue
            i = busca(pl_lineas, ai, lo, hi, cur)
            j = busca(pl_lineas, bi, lo, hi, i) if i else None
            if not i or not j:
                cual = f"el INICIO {ai[:60]!r}" if not i else f"el FIN {bi[:60]!r}"
                fallos.append(f"{e['destino']} (M{e.get('modulo')}) bloque {k}: no encuentro {cual} "
                              f"en la seccion {lo}-{hi}")
                nuevos.append(str(r))
                continue
            nuevos.append(f"{i}-{j}")
            cur = j
        if [str(x) for x in e["bloques"]] != nuevos:
            cambios.append((e["destino"], list(e["bloques"]), nuevos))

    for d, viejo, nuevo in cambios:
        print(f"  {d}: {viejo} -> {nuevo}")
    for f in fallos:
        print(f"  FALLO {f}")
    print(f"\n  {len(cambios)} entradas reubicadas, {len(fallos)} fallos")
    if fallos:
        print("  No escribo nada: un ancla que no aparece en su seccion es texto que cambio,")
        print("  y hay que corregirla a mano en mapeo.yaml.")
        return 1
    if a.escribir:
        txt = mapa.read_text(encoding="utf-8")
        for d, viejo, nuevo in cambios:
            v = f"bloques: [{', '.join(str(x) for x in viejo)}]"
            txt = txt.replace(v, f"bloques: [{', '.join(nuevo)}]", 1)
        txt = re.sub(r"^libro_lineas: \d+", f"libro_lineas: {len(lineas)}", txt, flags=re.M)
        mapa.write_text(txt, encoding="utf-8")
        print("  mapeo.yaml reescrito. Ahora extrae y COMPRUEBA QUE EL PYTHON COMPILA.")
    else:
        print("  Revisa el diff y vuelve con --escribir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
