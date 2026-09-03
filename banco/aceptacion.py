# aceptacion.py --- no escribe piezas nuevas: enciende las que ya
# tienes, todas a la vez, y cuenta. Lo único que se amplía es el
# evals/medidas.py del 15.7: cada función muestrea n casos del
# corpus con la semilla, los lanza contra el entrypoint real y
# devuelve una fracción de 0 a 1.
import subprocess
import sys

from evals.medidas import (
    Puerta, medir,      # el evaluador del 15.7: NO se reescribe
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

PUERTAS = {          # medida, casos, umbral de release, pases
    "recall@5":        (recall5, 120, 0.80, PASES_RECALL),
    "faithfulness":    (faithfulness, 120, 0.90, PASES),
    "chat_autonomo":   (chat_autonomo, 100, 0.85, PASES),
    "lote_sin_humano": (lote_sin_humano, 500, 0.85, PASES),
    "ahorro_humano":   (ahorro_vs_humano, 200, 0.60, PASES),
    "redteam":         (redteam, 40, 1.00, PASES),
}


if __name__ == "__main__":
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout
    print(f"commit {sha.strip()}  corpus {CORPUS}  semilla {SEMILLA}")
    ok = [medir(Puerta(n, *p, RUIDO), CORPUS, SEMILLA) == "PASA"
          for n, p in PUERTAS.items()]
    sys.exit(0 if all(ok) else 1)
