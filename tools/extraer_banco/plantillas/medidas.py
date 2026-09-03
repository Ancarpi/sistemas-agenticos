# medidas.py --- ANDAMIO. El libro NO entrega este fichero: es el
# Ejercicio 31.1, y lo dice en el propio comentario de `aceptacion.py`.
#
# Contrato que `aceptacion.py` (31.2) espera de cada medida:
#
#     medida(n: int, corpus: str, semilla: int) -> float   # 0..1
#
# Muestrea `n` casos del `corpus` con la `semilla` --- la semilla fija QUE
# casos se muestrean, no el ruido del modelo ---, los lanza contra el
# entrypoint REAL (no contra un mock) y devuelve la fraccion que pasa.
#
#   TODO Ejercicio 31.1: implementar las seis contra tus entrypoints.
#     recall5           Ej. 8.3 ampliado a 120 preguntas (indice congelado)
#     faithfulness      el rag_dataset v3 del 18.4
#     chat_autonomo     POST /chat/{cliente_id} del 12.5, sin escalado
#     lote_sin_humano   main() del 11.5: cerradas / entradas
#     ahorro_vs_humano  Ej. 17.4, contra tu coste humano por caso
#     redteam           los 40 del 18.4: Anexo I + los tuyos
#
# Al menos una puerta tiene que no pasar: si pasan las seis a la primera,
# los umbrales son decorativos (31.2).

_PENDIENTE = ("{}: sin implementar. Es el Ejercicio 31.1 --- se escribe "
              "contra tus entrypoints reales, y una medida falsa es peor "
              "que ninguna porque la puerta pasa igual.")


def _andamio(nombre):
    def medida(n: int, corpus: str, semilla: int) -> float:
        raise NotImplementedError(_PENDIENTE.format(nombre))
    medida.__name__ = nombre
    return medida


recall5 = _andamio("recall5")
faithfulness = _andamio("faithfulness")
chat_autonomo = _andamio("chat_autonomo")
lote_sin_humano = _andamio("lote_sin_humano")
ahorro_vs_humano = _andamio("ahorro_vs_humano")
redteam = _andamio("redteam")
