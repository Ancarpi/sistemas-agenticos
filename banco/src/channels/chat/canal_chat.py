# canal_chat.py --- el consumidor real: actividad y tokens a la vez.
# `grafo_conciliacion.py` es el fichero del 5.3, tecleado: sus
# nodos son triage, investigar, resolver, revision_humana y
# notificar, más el ToolNode, que no emite nada al usuario.
from grafo_conciliacion import obtener_app   # la fábrica del 5.3

# El estado NO se enseña: se traduce. Este diccionario es tu
# contrato de transparencia del 12.4, y es lista BLANCA: un nodo
# que no esté aquí no emite nada. Cuatro de los cinco que hablan:
# el quinto es `notificar`, y de ese el usuario ya recibe los
# tokens.
ETIQUETAS = {
    "triage": "Clasificando tu incidencia...",
    "investigar": "Consultando tus movimientos...",
    "resolver": "Aplicando la resolución...",
    "revision_humana": "Lo está revisando un compañero...",
}


async def canal_chat(pregunta: str, referencia: str, hilo: str):
    # El grafo se compila DENTRO de este loop (5.3): con el
    # checkpointer síncrono, `astream` muere en el primer
    # superpaso con NotImplementedError.
    app = await obtener_app()
    # La referencia va SIEMPRE: EstadoBackoffice la declara y el
    # nodo `investigar` la lee. Sin ella, KeyError a mitad de
    # grafo, con el triaje ya pagado.
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
