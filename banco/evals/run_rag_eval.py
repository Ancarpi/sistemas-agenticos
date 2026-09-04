# evals/run_rag_eval.py --- la puerta del 8.3: el conjunto dorado,
# las dos métricas de recuperación y el código de salida. El
# veredicto no se escribe aquí, lo da el `medir` del 15.7.
import sys
from math import log2

from evals.medidas import (Puerta, cargar, casos_para, juzga,
                           medir, recall_at_k)
from src.rag.rerank import recuperar
from src.rag.responder import responder

# El encabezado firma la corrida, igual que el aceptacion.py del
# 31.2: sin corpus ni semilla, un verde no se repite.
CORPUS = "manuales-2026-09"
SEMILLA = 31
K = 5                    # el AL_MODELO del 8.2, dicho otra vez
CASOS = 25               # las 25 preguntas del Ejercicio 8.3
UMBRAL_RECALL = 0.80     # los dos umbrales del 18.4, y el sys.exit
UMBRAL_FIEL = 0.90       # de abajo no mira nada más
CAIDA_RECALL = 0.05      # «> 5 pts» en la tabla del 18.4
CAIDA_FIEL = 0.04        # «> 4 pts» en la misma tabla
PASES_JUEZ = 3           # el juez no es determinista; el recall sí

# Una línea de evals/rag_dataset.v1.jsonl, y son seis campos
# porque los seis los lee alguien:
#   id          "q07", estable: es lo que se cita en un post-mortem
#   pregunta    la del cliente, con sus faltas y sin tildes
#   fuentes     ["tarifas/devoluciones-sepa-3"], los documentos
#               correctos, comparados contra meta["fuente"], que
#               es lo que el trozo del 7.3 escribe y lo que el
#               `recall5` del 15.7 ya lee de este mismo campo
#   referencia  la respuesta buena en una o dos frases, para el
#               juez del 15.7; nunca se compara con ==
#   nivel       "publica" o "publica,interna": con qué nivel se
#               pregunta, porque la RLS del 7.6 cambia el corpus y
#               un recall medido como dueño de la tabla mide un
#               sistema que nadie despliega
#   modalidad   "texto", "tabla" o "figura", el aviso del 8.5: sin
#               filas de las dos últimas no sabes si esa capa va


# `recall_at_k` ya no se define aquí: vive una sola vez, en el
# `medidas.py` del 15.7, porque el `recall5` de allí medía lo
# mismo con otra aritmética y sobre otro conjunto. Es la misma
# razón por la que este fichero toma de RAGAS la idea y no la
# dependencia, que es lo que dice el párrafo de encima.


def ndcg_at_k(orden: list[str], correctas: set[str],
              k: int = K) -> float:
    """El mismo acierto, descontado por el puesto en que sale y
    dividido por el del mejor orden posible: de 0 a 1. La fuente
    repetida cobraría dos veces el mismo acierto, así que el orden
    se deduplica antes de puntuar."""
    orden = list(dict.fromkeys(orden))
    dcg = sum(1 / log2(i + 1)
              for i, d in enumerate(orden[:k], start=1)
              if d in correctas)
    ideal = sum(1 / log2(i + 1)
                for i in range(1, min(len(correctas), k) + 1))
    return dcg / ideal if ideal else 0.0


FUSIONES: dict[str, list[str]] = {}


def orden(caso: dict) -> list[str]:
    """Las fuentes que el retriever del 8.2 pone delante, en su
    orden. Se cachea por caso porque sobre un índice congelado la
    lista no cambia, y sin la caché el nDCG vuelve a pagar las
    veinticinco recuperaciones que el recall acaba de pagar."""
    if caso["id"] not in FUSIONES:
        FUSIONES[caso["id"]] = [
            t["meta"]["fuente"] for t in
            recuperar(caso["pregunta"], niveles=caso["nivel"])]
    return FUSIONES[caso["id"]]


def recuperacion(metrica):
    """Adaptador a la firma que `medir` espera, (n, corpus,
    semilla) -> float, con la media sobre los n casos."""
    def medida(n: int, corpus: str, semilla: int) -> float:
        casos = cargar("rag_dataset", "v1", n, semilla)
        return sum(metrica(orden(c), set(c["fuentes"]), K)
                   for c in casos) / n
    return medida


def fidelidad(n: int, corpus: str, semilla: int) -> float:
    """La segunda puerta, la que el 8.3 llama faithfulness.

    Dos cosas la bajan y las dos cuentan igual: una cita que el
    modelo no recibió, que `comprobar` caza sin gastar juez, y una
    afirmación que el contexto no sostiene, que la caza el juez
    del 15.7 sobre el contexto RECUPERADO.
    """
    fieles = 0
    for c in cargar("rag_dataset", "v1", n, semilla):
        r = responder(c["pregunta"], niveles=c["nivel"])
        if r["defectos"]:
            continue
        fieles += juzga(c["pregunta"], r["contexto"],
                        c["referencia"], r["texto"]).fundamentada
    return fieles / n


PUERTAS = [
    Puerta("recall@5", recuperacion(recall_at_k), CASOS,
           UMBRAL_RECALL, 1, CAIDA_RECALL),
    Puerta("faithfulness", fidelidad, CASOS, UMBRAL_FIEL,
           PASES_JUEZ, CAIDA_FIEL),
]


if __name__ == "__main__":
    print(f"corpus {CORPUS}  semilla {SEMILLA}  k={K}"
          f"  casos {CASOS}")
    ok = [medir(p, CORPUS, SEMILLA) == "PASA" for p in PUERTAS]
    # El nDCG@5 se imprime aparte y sin umbral a propósito, para
    # explicar y no para bloquear. Dos configuraciones con el
    # mismo Recall@5 se separan aquí, y es la columna que se lee
    # cuando el reranker del 8.2 entra o sale.
    print(f"{'ndcg@5':<16}"
          f"{recuperacion(ndcg_at_k)(CASOS, CORPUS, SEMILLA):.3f}"
          f"  informativa, sin umbral")
    print(f"caída de {CAIDA_RECALL:.2f} sobre {UMBRAL_RECALL:.2f}:"
          f" {casos_para(CAIDA_RECALL, UMBRAL_RECALL)} casos")
    sys.exit(0 if all(ok) else 1)
