#!/usr/bin/env python3
"""nombres --- los nombres que el arbol USA y nadie define.

POR QUE EXISTE, y es la quinta leccion de la misma familia. El paquete tenia cuatro
comprobaciones y las cuatro daban verde sobre un `memoria.py` que no importaba:
`@tool` era un nombre indefinido en tres decoradores. El red team lo dijo mejor de
lo que yo lo diria: «compileall pasa porque parsea, e `imports.py` pasa porque
audita los nombres que se IMPORTAN y jamas los que se USAN».

Esta comprobacion cierra ese hueco delegando en `pyflakes`, que es una dependencia
de desarrollo y no del paquete. Y hace lo que `pyflakes` solo no puede: separar las
roturas de los **fragmentos que el libro declara como fragmentos**. El 0.1 lo
promete con estas palabras, «los fragmentos marcados como fragmentos», y un boceto
de firmas con el cuerpo en `...` no es un fichero roto: es un boceto. Lo que no
puede pasar es que un fichero que el libro presenta como entregado no importe.

    python3 nombres.py [--arbol ../../banco]
"""
import argparse
import pathlib
import re
import subprocess
import sys

import yaml

# Lo que pyflakes dice y no es un defecto: un import que el fichero deja para el
# lector, o un simbolo que el libro define en otro bloque del mismo fichero.
RUIDO = re.compile(r"imported but unused|unable to detect undefined names")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", default=str(pathlib.Path(__file__).parents[2] / "banco"))
    ap.add_argument("--fragmentos",
                    default=str(pathlib.Path(__file__).parent / "fragmentos.yaml"))
    a = ap.parse_args()

    declarados = {}
    ruta = pathlib.Path(a.fragmentos)
    if ruta.exists():
        for f in yaml.safe_load(ruta.read_text(encoding="utf-8")) or []:
            declarados[f["fichero"]] = f.get("localizador", "")

    try:
        salida = subprocess.run([sys.executable, "-m", "pyflakes", a.arbol],
                                capture_output=True, text=True).stdout
    except FileNotFoundError:
        print("  SALTADO: pyflakes no esta instalado (pip install pyflakes)")
        return 0

    roto, excusados = [], []
    for linea in salida.splitlines():
        if not linea.strip() or RUIDO.search(linea):
            continue
        fich = linea.split(":", 1)[0]
        rel = str(pathlib.Path(fich).relative_to(a.arbol)) if fich.startswith(a.arbol) else fich
        (excusados if rel in declarados else roto).append((rel, linea))

    print(f"  {len(roto) + len(excusados)} avisos de pyflakes sobre el arbol")
    if excusados:
        vistos = sorted({r for r, _ in excusados})
        print(f"  {len(excusados)} en {len(vistos)} fichero(s) que el libro declara fragmento:")
        for r in vistos:
            print(f"    - {r}: {declarados[r].strip()[:100]}")
    if not roto:
        print("  todos los nombres que el arbol usa estan definidos, o son de un")
        print("  fragmento que el libro declara como tal.")
        return 0
    print(f"\n  {len(roto)} NOMBRE(S) SIN DEFINIR EN FICHEROS QUE EL LIBRO ENTREGA:")
    for _, linea in roto:
        print(f"    {linea}")
    print("\n  Un nombre indefinido no lo ve `compileall` (el fichero parsea) ni")
    print("  `imports.py` (audita lo importado, no lo usado): se arregla en el libro,")
    print("  o el fichero se declara fragmento en fragmentos.yaml con su localizador.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
