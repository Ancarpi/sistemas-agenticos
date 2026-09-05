# src/rag/hibrida.py --- búsqueda híbrida sobre la tabla del 7.6.
import os
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

import psycopg

from src.core.models import get_embeddings   # la fábrica del 0.4

SQL = Path(__file__).with_name("hibrida.sql").read_text()
NIVELES = "publica"     # el coalesce del 7.6, dicho en voz alta.
K_RRF = 60      # Cormack, Clarke y Buettcher, SIGIR 2009.
N_RAMA = 30     # candidatos POR rama, antes de fusionar.


def rrf(listas: dict[str, list[str]], k: int = K_RRF,
        pesos: dict[str, float] | None = None,
        ) -> list[tuple[str, float]]:
    """RRF: score(d) = suma_r  peso_r / (k + rango_r(d)).

    El rango empieza en 1. Nunca entra la puntuación original de
    cada rama: por eso se pueden fusionar una distancia coseno y
    un ts_rank_cd, que no comparten ni escala ni sentido.
    """
    pesos = pesos or {}
    puntos: dict[str, float] = defaultdict(float)
    for rama, ids in listas.items():
        peso = pesos.get(rama, 1.0)
        for rango, doc_id in enumerate(ids, start=1):
            puntos[doc_id] += peso / (k + rango)
    return sorted(puntos.items(), key=lambda par: -par[1])


@contextmanager
def sesion_lectura(niveles: str = NIVELES):
    """El BEGIN del 7.6, traducido y en un solo sitio.

    Tiene que ser SET LOCAL: un SET a secas sobrevive a la
    petición, la conexión vuelve al pool y el siguiente cliente
    hereda el nivel del anterior. El rol no se parametriza --- es
    un nombre, no un valor ---, pero el nivel sí, y set_config con
    `true` de tercer argumento ES el SET LOCAL en forma de
    función. Los tres ajustes de HNSW van aquí por lo mismo que
    dice el 7.6: la política es otro post-filtro, y con dos
    encima del índice el freno del escaneo iterativo deja de ser
    un lujo.
    """
    # es_banco vive en banco y plainto_tsquery la busca por
    # nombre: sin este -c, el del pool del 10.2, no la encuentra.
    # Y public porque el tipo vector y su <=> viven allí: el
    # CREATE EXTENSION del 7.6 corre antes del SET search_path.
    with psycopg.connect(os.environ["DATABASE_URL"],
                         options="-c search_path=banco,public") as con:
        with con.transaction():
            con.execute("SET LOCAL ROLE agente_lectura")
            con.execute("SELECT set_config('banco.niveles',"
                        " %s, true)", (niveles,))
            con.execute("SET LOCAL hnsw.ef_search = 100")
            con.execute("SET LOCAL hnsw.iterative_scan ="
                        " 'relaxed_order'")
            con.execute("SET LOCAL hnsw.max_scan_tuples = 20000")
            yield con


def ramas(pregunta: str, tipo: str | None = None,
          producto: str | None = None, niveles: str = NIVELES,
          n_rama: int = N_RAMA) -> dict[str, list[str]]:
    """Las dos listas ordenadas, todavía sin fusionar."""
    vec = get_embeddings().embed_query(pregunta)
    with sesion_lectura(niveles) as con:
        # psycopg no sabe adaptar una lista de Python a vector: el
        # str() de la lista ya es la sintaxis que espera pgvector y
        # el ::vector de la consulta hace el resto.
        filas = con.execute(SQL, {"vec": str(vec), "texto": pregunta,
                                  "tipo": tipo, "producto": producto,
                                  "n_rama": n_rama}).fetchall()
    densa: dict[int, str] = {}
    lexica: dict[int, str] = {}
    for doc_id, r_densa, r_lexica in filas:
        if r_densa is not None:
            densa[r_densa] = str(doc_id)
        if r_lexica is not None:
            lexica[r_lexica] = str(doc_id)
    return {"densa": [densa[r] for r in sorted(densa)],
            "lexica": [lexica[r] for r in sorted(lexica)]}


def buscar_hibrido(pregunta: str, tipo: str | None = None,
                   producto: str | None = None,
                   niveles: str = NIVELES,
                   n_rama: int = N_RAMA) -> list[tuple[str, float]]:
    return rrf(ramas(pregunta, tipo, producto, niveles, n_rama))


def trozos(ids: list[str],
           niveles: str = NIVELES) -> dict[str, dict]:
    """Los textos, en un viaje --- y con el mismo rol puesto.

    Esta es la consulta que se olvida: la fusión ya respetó la
    política, y este SELECT, si sale de la transacción, entra
    como dueño de la tabla y sirve el trozo restringido. El
    ::uuid[] no defiende nada: psycopg manda la lista sin tipo
    y el = ANY ya la resuelve a uuid[]; el cast solo deja el
    tipo escrito para quien lea la consulta.
    """
    with sesion_lectura(niveles) as con:
        filas = con.execute(
            "SELECT langchain_id, content, fuente, seccion, "
            "clasificacion FROM banco.manuales "
            "WHERE langchain_id = ANY(%s::uuid[])",
            (ids,)).fetchall()
    return {str(i): {"id": str(i), "content": c,
                     "meta": {"fuente": f, "seccion": s,
                              "clasificacion": n}}
            for i, c, f, s, n in filas}


if __name__ == "__main__":
    import sys

    nivel = "publica,interna"     # el del empleado de oficina
    listas = ramas(sys.argv[1], niveles=nivel)
    puesto = {rama: {d: i for i, d in enumerate(ids, start=1)}
              for rama, ids in listas.items()}
    fusion = rrf(listas)
    print(f"densa {len(listas['densa'])}  léxica "
          f"{len(listas['lexica'])}  fusión {len(fusion)} únicos")
    cabeza = fusion[:8]
    texto = trozos([d for d, _ in cabeza], niveles=nivel)
    for n, (doc, score) in enumerate(cabeza, start=1):
        d = puesto["densa"].get(doc)
        x = puesto["lexica"].get(doc)
        etiqueta = "ambas" if d and x else "densa" if d else "léxica"
        print(f"{n:3d}  {score:.6f}  {etiqueta:8s}"
              f" {'d%s' % d if d else '--':4s}"
              f"{'l%s' % x if x else '--':4s}"
              f" {texto[doc]['meta']['fuente']}")
