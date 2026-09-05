#!/usr/bin/env python3
"""esquemas --- los .sql del arbol APLICAN, en su orden documentado.

POR QUE EXISTE. `tablas.py` pregunta si cada tabla usada tiene su CREATE
TABLE; nadie preguntaba si los .sql aplican. Y un .sql solo falla al
ejecutarlo: una POLICY contra un rol que aun no existe, un GRANT sobre una
tabla de otro fichero o un CHECK que rechaza el tipo que otro modulo
inserta pasan enteros por compileall, imports, nombres y tablas ---
gobierno.sql y el CHECK de registro_ia vivieron ahi. Esta comprobacion
crea una base LIMPIA, aplica los ficheros en el orden que el arbol
documenta (README y cabeceras), repite los que se declaran reaplicables y
tira la base al salir.

QUE NECESITA. Un Postgres con pgvector y la variable ESQUEMAS_URL (URL
admin: crea y borra una base efimera `esquemas_check_<pid>`). Sin la
variable SALTA con exit 0 y lo dice a gritos: el verde local sin
ESQUEMAS_URL no acredita esta comprobacion. En CI la acredita el service
container de promesas.yml.

    ESQUEMAS_URL=postgresql://postgres:pass@localhost:5432/postgres \
        python3 esquemas.py [--arbol ../../banco]
"""
import argparse
import os
import pathlib
import subprocess
import sys
import urllib.parse

# El orden documentado, como datos y UNA vez: el del libro, que es el que
# el README de banco/ y las cabeceras de los propios .sql cuentan.
#   - veces=2: el fichero se anuncia reaplicable, y eso tambien se cobra.
#   - consulta=True: es una query parametrizada (%(x)s), no DDL; se
#     ejecuta con literales inocuos sobre la base ya montada, porque su
#     promesa es que la consulta PLANIFICA contra ese esquema.
ORDEN = [
    ("db/schema.sql", 2, False),          # 7.6 + 16.6 + 21.5 + 35.6 + 34.7
    ("src/rag/08_hibrida.sql", 1, False), # 8.1: se ejecuta UNA vez
    ("src/rag/hibrida.sql", 1, True),     # 8.1: la consulta hibrida
    ("src/rag/gobierno.sql", 2, False),   # 24.6: reaplicable
    ("src/core/memoria.sql", 2, False),   # 34.7: reaplicable
]
LITERALES = {
    "%(vec)s": "'[" + ",".join(["1"] + ["0"] * 1023) + "]'",
    "%(tipo)s": "NULL",
    "%(producto)s": "NULL",
    "%(texto)s": "'comision por devolver una transferencia'",
    "%(n_rama)s": "50",
}


def psql(url: str, *args, entrada: str | None = None):
    return subprocess.run(
        ["psql", url, "-v", "ON_ERROR_STOP=1", "-X", "-q", *args],
        input=entrada, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", default=str(
        pathlib.Path(__file__).parents[2] / "banco"))
    a = ap.parse_args()
    arbol = pathlib.Path(a.arbol)

    admin = os.environ.get("ESQUEMAS_URL")
    if not admin:
        print("SALTADO: sin ESQUEMAS_URL no hay Postgres contra el que")
        print("aplicar los .sql. Esta comprobacion NO se ha ejecutado:")
        print("el verde no la acredita. Con un Postgres+pgvector a mano:")
        print("  ESQUEMAS_URL=postgresql://... python3 esquemas.py")
        return 0

    # Todo .sql del arbol esta en el orden documentado: uno nuevo sin
    # su sitio aqui es exactamente el fallo que esta comprobacion caza.
    en_orden = {f for f, _, _ in ORDEN}
    ignora = {".venv", "venv", "__pycache__", ".pytest_cache"}
    del_arbol = {str(p.relative_to(arbol))
                 for p in arbol.rglob("*.sql")
                 if not set(p.parts) & ignora}
    sueltos = sorted(del_arbol - en_orden)
    if sueltos or sorted(en_orden - del_arbol):
        for f in sueltos:
            print(f"  - {f}: .sql del arbol sin sitio en el ORDEN"
                  " documentado de esquemas.py")
        for f in sorted(en_orden - del_arbol):
            print(f"  - {f}: en el ORDEN de esquemas.py pero no en"
                  " el arbol")
        return 1

    base = f"esquemas_check_{os.getpid()}"
    r = psql(admin, "-c", f'CREATE DATABASE "{base}"')
    if r.returncode:
        print(f"ERROR: no se pudo crear {base} en ESQUEMAS_URL:")
        print("  " + (r.stderr.strip() or r.stdout.strip()))
        return 1
    partes = urllib.parse.urlsplit(admin)
    url = urllib.parse.urlunsplit(partes._replace(path="/" + base))

    fallos = 0
    try:
        for rel, veces, consulta in ORDEN:
            sql = (arbol / rel).read_text(encoding="utf-8")
            if consulta:
                for marca, lit in LITERALES.items():
                    sql = sql.replace(marca, lit)
                # La cabecera del fichero lo dice: va DENTRO de la
                # transaccion del 7.6, con su search_path ya puesto.
                sql = "SET search_path = banco, public;\n" + sql
            for pasada in range(1, veces + 1):
                r = psql(url, entrada=sql)
                tag = f" (pasada {pasada}: reaplicable)" if pasada > 1 \
                    else (" (consulta, con literales)" if consulta
                          else "")
                if r.returncode:
                    fallos += 1
                    print(f"  FALLA {rel}{tag}:")
                    for l in r.stderr.strip().splitlines():
                        print(f"    {l}")
                    break
                print(f"  OK    {rel}{tag}")
    finally:
        psql(admin, "-c", f'DROP DATABASE IF EXISTS "{base}"'
                          " WITH (FORCE)")

    if fallos:
        print(f"\n  {fallos} fichero(s) no aplican en el orden que el"
              " arbol documenta.")
        return 1
    print(f"\n  los {len(ORDEN)} .sql del arbol aplican en su orden"
          " documentado (base efimera creada y tirada).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
