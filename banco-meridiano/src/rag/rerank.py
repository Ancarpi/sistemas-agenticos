# src/rag/rerank.py --- el cross-encoder, servido por tu gateway.
import os

import httpx        # ya lo tienes: lo arrastra el cliente OpenAI

from src.rag.hibrida import NIVELES, buscar_hibrido, trozos

VENTANA = 40        # candidatos fusionados que ve el reranker
AL_MODELO = 5       # trozos que llegan al prompt del 7.5


def rerankear(pregunta: str, candidatos: list[dict],
              top_n: int = AL_MODELO) -> list[dict]:
    """Una pasada del cross-encoder sobre TODOS los candidatos.

    No hay nada que cachear entre preguntas: el cross-encoder lee
    pregunta y trozo juntos, así que su puntuación solo existe
    para este par. Por eso no se puede precalcular ni indexar, y
    por eso el coste es lineal en el número de candidatos.
    """
    r = httpx.post(
        f"{os.environ['OPENAI_API_BASE']}/rerank",
        headers={"Authorization":
                 f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={"model": "rerank-multilingue", "query": pregunta,
              "documents": [c["content"] for c in candidatos],
              "top_n": top_n},
        timeout=2.0,          # el presupuesto del 29.2 manda
    )
    r.raise_for_status()
    return [dict(candidatos[x["index"]], score=x["relevance_score"])
            for x in r.json()["results"]]


def recuperar(pregunta: str, tipo: str | None = None,
              producto: str | None = None,
              niveles: str = NIVELES) -> list[dict]:
    """Híbrido -> RRF -> cross-encoder -> lo que ve el modelo.

    El nivel acompaña a las dos lecturas. Un reranker no puede
    reordenar lo que el retriever ocultó, y no debe verlo.
    """
    fusion = buscar_hibrido(pregunta, tipo, producto, niveles)
    ids = [i for i, _ in fusion[:VENTANA]]
    texto = trozos(ids, niveles)
    # Se rerankea en el orden de la fusión: si el reranker cae, el
    # degradado natural es servir esta misma lista sin reordenar.
    orden = [texto[i] for i in ids if i in texto]
    if not orden:
        return []
    try:
        return rerankear(pregunta, orden)
    except httpx.HTTPError as err:
        print(f"reranker caído ({err}); sirvo la fusión cruda")
        # El score explícito a 0.0 mantiene el contrato de salida
        # y dice lo que hay: esto no lo ha puntuado nadie.
        return [dict(t, score=0.0) for t in orden[:AL_MODELO]]


if __name__ == "__main__":
    import sys

    for n, t in enumerate(recuperar(sys.argv[1]), start=1):
        print(f"{n}  {t['score']:.3f}  {t['meta']['fuente']}")
