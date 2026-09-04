# src/rag/gobierno.py --- frescura, procedencia y permisos de
# trozo sobre el retriever del 8.1. Antes: el gobierno.sql.
import os
from datetime import date

import psycopg

from src.rag.hibrida import (NIVELES, buscar_hibrido,
                             sesion_lectura, trozos)

# El inventario agrupa por DOCUMENTO y versión, no por trozo:
# nadie renueva 400 filas, se renueva un manual. `caduca_el` sale
# del gobierno.sql, y se repite en el HAVING porque un HAVING no
# puede referirse al alias del SELECT.
CADUCADOS = """
SELECT fuente, version, tipo,
       coalesce(aprobado_por, '(sin firma)') AS dueno,
       count(*) AS trozos,
       min(caduca_el(tipo, indexado_en, valid_to)) AS caduca
  FROM banco.manuales
 GROUP BY fuente, version, tipo, aprobado_por
HAVING min(caduca_el(tipo, indexado_en, valid_to))
       <= current_date + %(aviso)s::int
 ORDER BY caduca
"""

# La ficha de un trozo: de dónde salió, qué versión, quién firmó
# y hasta cuándo vale. Es lo que se enseña en una reclamación.
FICHA = """
SELECT langchain_id, fuente, seccion, version, clasificacion,
       aprobado_por, aprobado_en,
       caduca_el(tipo, indexado_en, valid_to) AS caduca
  FROM banco.manuales
 WHERE langchain_id = ANY(%s::uuid[])
"""
CAMPOS = ("fuente", "seccion", "version", "clasificacion",
          "aprobado_por", "aprobado_en", "caduca")


def caducados(dias_aviso: int = 30) -> list[dict]:
    """Lo caducado y lo que caduca dentro de `dias_aviso`.

    La conexión NO es `sesion_lectura()`, y esa es la trampa del
    fichero: `manuales_vigentes` le esconde a `agente_lectura`
    justo las filas que hay que listar. Escrito sobre la sesión
    de lectura, esto devuelve cero filas siempre, y cero se lee
    como «no hay nada caducado».
    """
    with psycopg.connect(os.environ["DATABASE_URL"],
                         options="-c search_path=banco") as con:
        filas = con.execute(CADUCADOS,
                            {"aviso": dias_aviso}).fetchall()
    hoy = date.today()
    return [{"fuente": f, "version": v, "tipo": t, "dueno": d,
             "trozos": n, "dias": (c - hoy).days}
            for f, v, t, d, n, c in filas]


def procedencia(ids: list[str],
                niveles: str = NIVELES) -> dict[str, dict]:
    """Las fichas de los trozos que ese usuario puede ver.

    Dentro de `sesion_lectura()` por lo mismo que `trozos()` en
    el 8.1: la ficha también es contenido, y pedirla con otra
    conexión reabre la fuga por las citas.
    """
    with sesion_lectura(niveles) as con:
        filas = con.execute(FICHA, (ids,)).fetchall()
    return {str(r[0]): dict(zip(CAMPOS, r[1:])) for r in filas}


def cita(f: dict) -> str:
    """Sin aprobador, la cita es «lo dice el manual», que en una
    reclamación no lo dice nadie."""
    return (f"[{f['fuente']} / {f['seccion']} v{f['version']}"
            f" · aprobado por {f['aprobado_por']}"
            f" el {f['aprobado_en']}"
            f" · vigente hasta {f['caduca'] or 'sin fecha'}]")


def contexto(pregunta: str, niveles: str = NIVELES,
             k: int = 5) -> tuple[list[dict], dict]:
    """Lo que entra en el prompt, y la cuenta de lo que no.

    Tres consultas con el mismo `niveles` y ninguna sobra: la
    fusión aplica la política, `trozos()` la vuelve a aplicar
    porque es otra consulta, y la ficha decide si el trozo se
    puede citar.
    """
    fusion = buscar_hibrido(pregunta, niveles=niveles)
    ids = [d for d, _ in fusion[:k]]
    texto, fichas = trozos(ids, niveles), procedencia(ids, niveles)
    usados: list[dict] = []
    fuera = {"revocado": 0, "sin_firma": 0}
    for doc in ids:
        if doc not in texto or doc not in fichas:
            # Con el mismo `niveles` en las tres, esto es cero.
            # Deja de serlo si alguien reclasifica el trozo entre
            # la fusión y el SELECT, y entonces la respuesta se
            # está montando sobre un permiso ya revocado.
            fuera["revocado"] += 1
            continue
        if not fichas[doc]["aprobado_por"]:
            fuera["sin_firma"] += 1
            continue
        usados.append({"texto": texto[doc]["content"],
                       "cita": cita(fichas[doc])})
    return usados, fuera


if __name__ == "__main__":
    import sys

    for nivel in ("publica", "publica,interna,restringida"):
        usados, fuera = contexto(sys.argv[1], niveles=nivel)
        print(f"\n[{nivel}] {len(usados)} citables,"
              f" {sum(fuera.values())} fuera {fuera}")
        for u in usados:
            print("  " + u["cita"])
    print("\nCADUCADO O A MENOS DE 30 DÍAS")
    for c in caducados():
        print(f"  {c['dias']:>5}d  {c['fuente']} v{c['version']}"
              f"  {c['trozos']:>3} trozos  {c['dueno']}")
