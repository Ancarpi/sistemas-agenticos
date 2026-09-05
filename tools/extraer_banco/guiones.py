#!/usr/bin/env python3
"""guiones --- lo que un bloque `if __name__` usa ya existe cuando corre.

POR QUE EXISTE. Un guion se ejecuta de arriba abajo: cuando un bloque
`if __name__ == "__main__"` corre, lo definido DESPUES de el aun no
existe. Es el orden que `batch_nocturno.py` (11.5) violaba: su bloque
main llama a `main()`, y `main()` cierra imprimiendo `informe()`,
definido dos lineas DESPUES del bloque --- arrancado como guion, un
NameError con `compileall` en verde (parsea), `imports.py` en verde (los
modulos resuelven) y `nombres.py` en verde (pyflakes ve el nombre en el
fichero). Ninguna de las anteriores pregunta por el ORDEN; esta si.

QUE COMPRUEBA. No exige que el bloque sea la ultima sentencia --- los
anadidos `modo: patch` del extractor viven detras del `__main__` de su
fichero base a proposito, y eso es sano mientras nada anterior los use.
La regla es el peligro real: para cada bloque `__main__`, ningun nombre
referenciado HASTA ese bloque (cuerpos de funcion incluidos, que el main
los llama) puede estar definido SOLO despues. Los ficheros que
`fragmentos.yaml` declara andamio se saltan, como en `nombres.py`.

    python3 guiones.py [--arbol ../../banco]
"""
import argparse
import ast
import pathlib
import sys

import yaml

IGNORA = {".venv", "venv", ".git", "__pycache__", ".pytest_cache",
          ".mypy_cache", ".ruff_cache", "node_modules", "site-packages"}


def es_bloque_main(nodo) -> bool:
    if not isinstance(nodo, ast.If):
        return False
    t = nodo.test
    if not (isinstance(t, ast.Compare) and len(t.ops) == 1
            and isinstance(t.ops[0], ast.Eq)):
        return False
    lados = [t.left] + list(t.comparators)
    nombres = {n.id for n in lados if isinstance(n, ast.Name)}
    valores = {c.value for c in lados if isinstance(c, ast.Constant)}
    return "__name__" in nombres and "__main__" in valores


def definidos(nodos):
    """Nombres que un tramo de sentencias top-level deja definidos."""
    defs = set()
    for n in nodos:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            defs.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            objetivos = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in objetivos:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        defs.add(x.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                defs.add((al.asname or al.name).split(".")[0])
    return defs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", default=str(
        pathlib.Path(__file__).parents[2] / "banco"))
    ap.add_argument("--fragmentos", default=str(
        pathlib.Path(__file__).parent / "fragmentos.yaml"))
    a = ap.parse_args()
    arbol = pathlib.Path(a.arbol)

    andamios = set()
    ruta = pathlib.Path(a.fragmentos)
    if ruta.exists():
        for f in yaml.safe_load(ruta.read_text(encoding="utf-8")) or []:
            andamios.add(f["fichero"])

    con_main, fallos, saltados = 0, [], []
    for p in sorted(arbol.rglob("*.py")):
        if set(p.parts) & IGNORA:
            continue
        rel = str(p.relative_to(arbol))
        arb = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        mains = [i for i, n in enumerate(arb.body) if es_bloque_main(n)]
        if not mains:
            continue
        if rel in andamios:
            saltados.append(rel)
            continue
        con_main += 1
        for i in mains:
            usados = {x.id for n in arb.body[: i + 1]
                      for x in ast.walk(n)
                      if isinstance(x, ast.Name)
                      and isinstance(x.ctx, ast.Load)}
            tarde = (usados & definidos(arb.body[i + 1:])) \
                - definidos(arb.body[: i + 1])
            if tarde:
                fallos.append((rel, arb.body[i].lineno,
                               ", ".join(sorted(tarde))))
    print(f"  {con_main} guiones con bloque __main__ revisados"
          + (f" ({len(saltados)} andamios saltados)" if saltados else ""))
    if fallos:
        print(f"\n  {len(fallos)} bloque(s) __main__ que usan nombres"
              " definidos DESPUES (NameError tras pagar el trabajo):")
        for f, linea, que in fallos:
            print(f"    - {f}: __main__ en L{linea} usa {que}")
        print("\n  El orden lo fija el libro: se corrige alli (o en"
              " mapeo.yaml) y se reextrae.")
        return 1
    print("  todo lo que cada bloque __main__ usa existe ya cuando"
          " corre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
