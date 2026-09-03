#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_test.py --- el cimiento del Ejercicio 0.1.

Cuatro comprobaciones y un resumen tabulado: dos alias distintos del
gateway con su latencia y sus tokens, la conexion a Postgres, y que la
traza salio con el nombre del proyecto. Si el proxy cae, el error es una
linea legible y no un traceback de cuarenta.

    uv run python smoke_test.py

Sale con 0 si las cuatro pasan; con 1 en cuanto una falla.
"""

import os
import sys
import time

ALIAS = ("agente-rapido", "agente-equilibrado")
PREGUNTA = "Responde solo con la palabra: listo."
FILAS = []


def fila(nombre, ok, detalle):
    FILAS.append((nombre, "OK " if ok else "FALLA", detalle))
    return ok


def falta(*variables):
    """Un .env a medias es el fallo mas frecuente del dia uno."""
    return [v for v in variables if not os.environ.get(v)]


def probar_alias(alias):
    ausentes = falta("OPENAI_API_BASE", "OPENAI_API_KEY")
    if ausentes:
        return fila(f"alias {alias}", False, f"falta en el .env: {', '.join(ausentes)}")
    try:
        from src.core.models import get_model
        t0 = time.perf_counter()
        r = get_model(alias).invoke(PREGUNTA)
        ms = int((time.perf_counter() - t0) * 1000)
    except Exception as e:                       # noqa: BLE001 --- una linea, no un traceback
        return fila(f"alias {alias}", False, f"{type(e).__name__}: {str(e).splitlines()[0][:90]}")
    uso = getattr(r, "usage_metadata", None) or {}
    return fila(f"alias {alias}", True,
                f"{ms} ms, entrada {uso.get('input_tokens', '?')}, "
                f"salida {uso.get('output_tokens', '?')}")


def probar_postgres():
    if falta("DATABASE_URL"):
        return fila("postgres", False, "falta DATABASE_URL en el .env")
    try:
        import psycopg
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as cx:
            version = cx.execute("select version()").fetchone()[0].split(",")[0]
            vector = cx.execute(
                "select 1 from pg_extension where extname = 'vector'").fetchone()
    except Exception as e:                       # noqa: BLE001
        return fila("postgres", False, f"{type(e).__name__}: {str(e).splitlines()[0][:90]}")
    if not vector:
        return fila("postgres", False,
                    f"{version} conecta, pero falta la extension vector "
                    f"(db/schema.sql la crea)")
    return fila("postgres", True, f"{version}, pgvector presente")


def probar_traza():
    """La traza no se comprueba llamando a LangSmith: se comprueba que el
    proceso esta configurado para emitirla. Que aparezca en el panel con el
    nombre del proyecto lo miras tu, una vez."""
    ausentes = falta("LANGSMITH_TRACING", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT")
    if ausentes:
        return fila("traza", False, f"falta en el .env: {', '.join(ausentes)}")
    if os.environ["LANGSMITH_TRACING"].lower() not in ("1", "true", "yes"):
        return fila("traza", False, "LANGSMITH_TRACING no esta en true: no se traza nada")
    return fila("traza", True,
                f"proyecto {os.environ['LANGSMITH_PROJECT']} --- "
                f"confirma en el panel que aparece la llamada de arriba")


def main():
    for alias in ALIAS:
        probar_alias(alias)
    probar_postgres()
    probar_traza()
    ancho = max(len(n) for n, _, _ in FILAS)
    print()
    for nombre, estado, detalle in FILAS:
        print(f"  {nombre:<{ancho}}  {estado}  {detalle}")
    fallan = [n for n, e, _ in FILAS if e.strip() == "FALLA"]
    print(f"\n  {len(FILAS) - len(fallan)}/{len(FILAS)} pasan"
          + (f"; revisa: {', '.join(fallan)}" if fallan else ""))
    return 1 if fallan else 0


if __name__ == "__main__":
    sys.exit(main())
