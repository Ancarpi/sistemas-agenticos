#!/usr/bin/env python3
"""tablas --- toda tabla banco.X que el arbol usa tiene su CREATE TABLE.

POR QUE EXISTE. La novena medicion: 29 sentencias SQL del arbol leian o
escribian `banco.trabajos`, `banco.aprobaciones`, `banco.efectos` y
`banco.supresiones` con las seis comprobaciones en verde, y ninguna de las
cuatro tablas existia en ningun .sql del arbol. `imports.py` audita modulos,
`nombres.py` nombres de Python: nadie preguntaba por los nombres de SQL.

QUE COMPRUEBA. Cada identificador `banco.X` que aparezca tras FROM, INTO,
UPDATE o JOIN en cualquier .py o .sql del arbol tiene un `CREATE TABLE`
(con o sin el prefijo `banco.`: db/schema.sql fija `search_path = banco`)
en algun .sql del arbol. Exit 1 con la lista de las que falten.

    python3 tablas.py [--arbol ../../banco]
"""
import argparse
import pathlib
import re
import sys

USO = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+banco\.([a-z_][a-z0-9_]*)", re.I)
CREA = re.compile(r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:banco\.)?([a-z_][a-z0-9_]*)", re.I)
IGNORA = {".venv", "venv", ".git", "__pycache__", ".pytest_cache",
          ".mypy_cache", ".ruff_cache", "node_modules", "site-packages"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", default=str(pathlib.Path(__file__).parents[2] / "banco"))
    a = ap.parse_args()
    arbol = pathlib.Path(a.arbol)

    usadas, creadas = {}, set()
    for p in sorted(arbol.rglob("*")):
        if p.suffix not in (".py", ".sql") or set(p.parts) & IGNORA:
            continue
        texto = p.read_text(encoding="utf-8", errors="replace")
        for t in USO.findall(texto):
            usadas.setdefault(t.lower(), str(p.relative_to(arbol)))
        if p.suffix == ".sql":
            creadas.update(t.lower() for t in CREA.findall(texto))

    faltan = sorted(t for t in usadas if t not in creadas)
    print(f"  {len(usadas)} tablas banco.* usadas, {len(creadas)} CREATE TABLE en los .sql del arbol")
    if faltan:
        print(f"\n  {len(faltan)} SIN CREATE TABLE en ningun .sql del arbol:")
        for t in faltan:
            print(f"    - banco.{t}  (usada en {usadas[t]}, entre otros)")
        print("\n  Su DDL esta en el libro: anade la entrada a mapeo.yaml (destino")
        print("  db/schema.sql, modo patch) y vuelve a extraer.")
        return 1
    print("  toda tabla banco.* que el arbol usa tiene su CREATE TABLE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
