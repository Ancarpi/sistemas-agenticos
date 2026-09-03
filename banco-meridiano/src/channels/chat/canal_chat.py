# canal_chat.py --- el consumidor real: actividad y tokens a la vez.
# `grafo_conciliacion.py` no es el fragmento de tres nodos del
# 5.1: es el grafo entero que compilas en el Ejercicio 5.1, con
# triage, investigar, resolver, revision_humana y notificar.
from grafo_conciliacion import app

# El estado NO se enseña: se traduce. Este diccionario es tu
# contrato de transparencia del 12.4, y es lista BLANCA: un nodo
# que no esté aquí no emite nada. Cuatro de los cinco: el quinto
# es `notificar`, y de ese el usuario ya recibe los tokens.
ETIQUETAS = {
    "triage": "Clasificando tu incidencia...",
    "investigar": "Consultando tus movimientos...",
    "resolver": "Aplicando la resolución...",
    "revision_humana": "Lo está revisando un compañero...",
}


async def canal_chat(pregunta: str, referencia: str, hilo: str):
    # La referencia va SIEMPRE: EstadoBackoffice la declara y el
    # nodo `triage` la lee. Sin ella, KeyError en el primer nodo.
    entrada = {"referencia": referencia,
               "messages": [("human", pregunta)]}
    async for modo, dato in app.astream(
            entrada, {"configurable": {"thread_id": hilo}},
            stream_mode=["updates", "messages"]):
        if modo == "updates":
            etiqueta = ETIQUETAS.get(next(iter(dato)))
            if etiqueta:
                yield {"tipo": "actividad", "texto": etiqueta}
        else:
            chunk, meta = dato
            if meta["langgraph_node"] == "notificar" and chunk.content:
                yield {"tipo": "token", "texto": chunk.content}
