# aceptacion.py --- no escribe piezas nuevas: enciende las que ya
# tienes, todas a la vez, y cuenta. Lo único añadido es
# evals/medidas.py: cada función muestrea n casos del corpus con la
# semilla, los lanza contra el entrypoint real y devuelve una
# fracción de 0 a 1.
import statistics
import subprocess
import sys

from evals.medidas import (
    ahorro_vs_humano,   # Ej. 17.4, contra tu coste humano por caso
    chat_autonomo,      # POST /chat/{cliente_id} del 12.5, sin escalado
    faithfulness,       # el `rag_dataset` v3 del 18.4
    lote_sin_humano,    # main() del 11.5: cerradas / entradas
    recall5,            # Ej. 8.3 ampliado a los 120 del 18.4
    redteam,            # los 40 del 18.4: Anexo I + los tuyos
)

CORPUS = "manuales-2026-09"   # la colección versionada del 24.1
SEMILLA = 31       # fija QUÉ casos se muestrean, no el ruido del LLM
PASES = 3          # 15.6: un pase es una observación, no una medida
PASES_RECALL = 1   # excepción del 18.4: sobre índice congelado la
                   # recuperación es determinista y repetir no informa
RUIDO = 0.03       # por debajo de esto, la diferencia no es real

PUERTAS = {                       # medida, casos, umbral, pases
    "recall@5":        (recall5, 120, 0.80, PASES_RECALL),
    "faithfulness":    (faithfulness, 120, 0.92, PASES),
    "chat_autonomo":   (chat_autonomo, 100, 0.85, PASES),
    "lote_sin_humano": (lote_sin_humano, 500, 0.85, PASES),
    "ahorro_humano":   (ahorro_vs_humano, 200, 0.60, PASES),
    "redteam":         (redteam, 40, 1.00, PASES),
}


def veredicto(nombre, medida, n, minimo, pases) -> bool:
    v = sorted(medida(n, CORPUS, SEMILLA) for _ in range(pases))
    media, lo, hi = statistics.fmean(v), v[0], v[-1]
    # La fila que casi nadie escribe: la media pasa y el intervalo
    # cruza el umbral. Eso no es «pasa», es NO CONCLUYENTE, y lo
    # que toca entonces es ampliar la muestra --- no debatirlo.
    if lo < minimo <= hi and hi - lo > RUIDO:
        estado = "NO CONCLUYENTE"
    else:
        estado = "PASA" if media >= minimo else "FALLA"
    print(f"{nombre:<16}{media:.3f} [{lo:.3f}-{hi:.3f}] n={n}"
          f" x{pases} min={minimo:.2f}  {estado}")
    return estado == "PASA"


if __name__ == "__main__":
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout
    print(f"commit {sha.strip()}  corpus {CORPUS}  semilla {SEMILLA}")
    ok = [veredicto(n, *p) for n, p in PUERTAS.items()]
    sys.exit(0 if all(ok) else 1)
