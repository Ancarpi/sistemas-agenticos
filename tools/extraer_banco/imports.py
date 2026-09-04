#!/usr/bin/env python3
"""imports --- comprueba que los imports internos del arbol resuelven.

POR QUE EXISTE. `integridad.py` garantiza que cada fichero sale entero, y
`compileall` que parsea. Ninguna de las dos responde la pregunta que un lector hace
al primer minuto: si `from grafo_voz import construir_cerebro` encuentra algo. El
red team de la septima medicion conto nueve imports internos apuntando a nombres
que no estaban en el arbol, con los tres verificadores en verde.

QUE COMPRUEBA. Por cada `from X import a, b` o `import X` donde `X` sea un modulo
del propio arbol (y no una dependencia de PyPI), que el fichero existe y que define
los nombres que se le piden. Resuelve tanto la forma de raiz (`from grafo_voz
import ...`, que es como importa la Parte I, con los ficheros en el mismo
directorio) como la forma de paquete (`from src.core.politica import ...`, la de
las Partes II y III).

    python3 imports.py [--arbol ../../banco]
"""
import argparse
import ast
import pathlib
import sys

# Lo que viene de PyPI o de la stdlib no es asunto de este script.
EXTERNO = {
    "os", "sys", "re", "json", "time", "random", "hashlib", "hmac", "base64",
    "argparse", "pathlib", "asyncio", "logging", "datetime", "typing",
    "dataclasses", "collections", "contextlib", "functools", "itertools",
    "math", "statistics", "subprocess", "tempfile", "textwrap", "unicodedata",
    "uuid", "decimal", "enum", "abc", "io", "csv", "sqlite3", "importlib",
    "yaml", "psycopg", "pydantic", "httpx", "fastapi", "uvicorn", "pytest",
    "langchain", "langchain_core", "langchain_openai", "langchain_postgres",
    "langgraph", "langsmith", "livekit", "mcp", "ragas", "numpy", "dotenv",
    "slack_sdk", "requests", "boto3", "redis", "prometheus_client", "cohere",
    "operator", "signal", "socket", "shutil", "threading", "traceback",
    "psycopg_pool", "langchain_mcp_adapters", "pipecat", "opentelemetry",
    "jinja2", "tiktoken", "sqlalchemy", "alembic", "croniter", "jwt",
}


# Directorios que no son del arbol aunque vivan dentro: el QUICKSTART manda al
# lector crear su entorno virtual justo aqui, y un `.venv` de 600 MB hace que
# las comprobaciones que recorren el arbol tarden minutos en vez de segundos.
IGNORA = {".venv", "venv", ".git", "__pycache__", "node_modules",
          ".pytest_cache", ".mypy_cache", ".ruff_cache", "site-packages"}


def del_arbol(p):
    return not (set(p.parts) & IGNORA)


def raiz(modulo):
    return (modulo or "").split(".")[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", default=str(pathlib.Path(__file__).parents[2] / "banco"))
    ap.add_argument("--deudas", default=str(pathlib.Path(__file__).parent / "deudas.yaml"))
    a = ap.parse_args()
    arbol = pathlib.Path(a.arbol)

    # Las deudas declaradas: piezas que el libro deja al lector a proposito y dice
    # donde. No son imports rotos, y separarlas es lo que hace que uno roto de
    # verdad no se pierda entre ellas.
    import yaml as _y
    deudas, localiza = {}, {}
    for d in (_y.safe_load(pathlib.Path(a.deudas).read_text(encoding="utf-8")) or []):
        deudas[d["modulo"]] = set(d["nombres"])
        localiza[d["modulo"]] = d.get("localizador", "")

    ficheros = sorted(p for p in arbol.rglob("*.py") if del_arbol(p))
    # Indice doble: por ruta de paquete y por nombre suelto, porque el libro usa
    # las dos formas a proposito (la Parte I tiene el arbol plano).
    define, por_nombre = {}, {}
    for p in ficheros:
        rel = p.relative_to(arbol)
        try:
            t = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        nombres = set()
        for n in ast.walk(t):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nombres.add(n.name)
            elif isinstance(n, ast.Assign):
                nombres |= {x.id for x in n.targets if isinstance(x, ast.Name)}
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                nombres.add(n.target.id)
        clave = str(rel.with_suffix("")).replace("/", ".")
        define[clave] = nombres
        por_nombre.setdefault(rel.stem, set()).update(nombres)

    roto, revisados, declaradas = [], 0, []
    for p in ficheros:
        rel = p.relative_to(arbol)
        try:
            t = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for n in ast.walk(t):
            if isinstance(n, ast.ImportFrom):
                mod = n.module or ""
                if raiz(mod) in EXTERNO or n.level:
                    continue
                # `from src.core import hitl` importa el MODULO src/core/hitl.py,
                # no un simbolo de un src/core.py que nadie escribe. Si todos los
                # nombres pedidos son modulos del arbol, el import resuelve.
                submods = [al.name for al in n.names
                           if f"{mod}.{al.name}" in define]
                if submods and len(submods) == len(n.names):
                    revisados += 1
                    continue
                if mod not in define and mod.split(".")[-1] not in por_nombre:
                    roto.append((rel, f"from {mod} import ...", "no hay ese modulo en el arbol"))
                    continue
                disponibles = define.get(mod) or por_nombre.get(mod.split(".")[-1], set())
                revisados += 1
                pedidos = [al.name for al in n.names
                           if al.name != "*" and al.name not in disponibles]
                clave = mod if mod in deudas else mod.split(".")[-1]
                debidos = [x for x in pedidos if x in deudas.get(clave, set())]
                faltan = [x for x in pedidos if x not in deudas.get(clave, set())]
                if debidos:
                    declaradas.append((rel, clave, debidos))
                if faltan:
                    roto.append((rel, f"from {mod} import {', '.join(faltan)}",
                                 "ese modulo no define esos nombres"))
            elif isinstance(n, ast.Import):
                for al in n.names:
                    if raiz(al.name) in EXTERNO:
                        continue
                    if al.name not in define and al.name.split(".")[-1] not in por_nombre:
                        roto.append((rel, f"import {al.name}", "no hay ese modulo en el arbol"))

    print(f"  {len(ficheros)} ficheros · {revisados} imports internos resueltos")
    if declaradas:
        print(f"  {len(declaradas)} imports apuntan a DEUDAS DECLARADAS del libro:")
        for rel, clave, nombres in declaradas:
            print(f"    - {rel}: {', '.join(nombres)} (de `{clave}`)")
            if localiza.get(clave):
                print(f"        declarado en {localiza[clave].strip()}")
    if not roto:
        print("  todos los imports internos del arbol resuelven.")
        return 0
    print(f"\n  {len(roto)} IMPORTS QUE NO RESUELVEN:")
    for rel, linea, motivo in roto:
        print(f"    - {rel}: `{linea}` --- {motivo}")
    print("\n  Un import roto no lo ve `compileall` (el fichero parsea) ni")
    print("  `integridad.py` (el bloque esta entero): se arregla en el libro.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
