#!/usr/bin/env python3
"""cobertura --- comprueba que el mapeo no se deja ningun fichero del libro.

POR QUE EXISTE. `extraer_banco.py --verificar` comprueba que las anclas del mapeo
siguen apuntando a lo que decian, y con eso responde «OK, anclas al dia». Lo que no
puede responder es si FALTA una entrada: solo mira lo que su propio mapeo nombra, asi
que una seccion «entregado» que nadie mapeo nunca es invisible para el. Paso: cuatro
ficheros de la Parte III --- `estado.py`, `registro.py`, `catalogo.py` y `trazas.py`,
los dos ultimos las unicas secciones «entregado» de esa parte --- estuvieron en el
libro y fuera del repositorio mientras el verificador daba OK y salia con cero.

QUE COMPRUEBA. Todo bloque de codigo del libro cuya primera linea es un comentario con
nombre de fichero (`# algo.py --- ...`, `-- algo.sql ---`) declara una entrega, y una
entrega tiene que tener destino en el mapeo. Lo que no lo tiene sale listado.

    python3 cobertura.py --libro ../../fuente/libro.md
"""
import argparse
import pathlib
import re
import sys

import yaml

# Un bloque cuya cabecera nombra un fichero es una entrega; los demas son fragmentos
# didacticos y no tienen por que estar en el arbol.
CABECERA = re.compile(r"^\s*(?:#|--)\s*([A-Za-z0-9_./-]+\.(?:py|sql|ya?ml|toml|sh))\b")


def entregas(lineas):
    """(nombre de fichero, linea) por cada bloque que se presenta con nombre."""
    out, dentro = [], False
    for i, l in enumerate(lineas):
        if l.startswith("```"):
            dentro = not dentro
            if dentro:
                # la cabecera es la primera linea no vacia del bloque
                for j in range(i + 1, min(i + 4, len(lineas))):
                    if not lineas[j].strip():
                        continue
                    m = CABECERA.match(lineas[j])
                    if m:
                        out.append((m.group(1), j + 1))
                    break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--libro", required=True)
    ap.add_argument("--mapeo", default=str(pathlib.Path(__file__).parent / "mapeo.yaml"))
    a = ap.parse_args()

    lineas = pathlib.Path(a.libro).read_text(encoding="utf-8").split("\n")
    m = yaml.safe_load(pathlib.Path(a.mapeo).read_text(encoding="utf-8"))
    destinos = {pathlib.Path(e["destino"]).name for e in m["entradas"]}

    faltan = []
    for nombre, linea in entregas(lineas):
        if pathlib.Path(nombre).name not in destinos:
            faltan.append((nombre, linea))

    vistos = len(entregas(lineas))
    print(f"  {vistos} bloques del libro se presentan con nombre de fichero")
    print(f"  {len(destinos)} destinos distintos en el mapeo")
    if faltan:
        print(f"\n  {len(faltan)} SIN ENTRADA EN EL MAPEO --- estan en el libro y no en el arbol:")
        for nombre, linea in faltan:
            print(f"    - {nombre}  (libro.md:{linea})")
        print("\n  Anade su entrada a mapeo.yaml, o justifica en la nota por que ese")
        print("  bloque es un fragmento didactico y no una entrega.")
        return 1
    print("  cobertura completa: todo bloque con nombre de fichero tiene destino.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
