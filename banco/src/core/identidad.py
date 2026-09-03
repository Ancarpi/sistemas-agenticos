# identidad.py --- lo único nuevo: el thread_id lo decide aquí.
GRAFOS = {"conciliacion", "voz"}      # los dos del sistema


def hilo(grafo: str, sujeto: str) -> str:
    """El sujeto lleva su clase delante --- `cliente:C-99`,
    `incidencia:REF-4471` ---, o chocarán. Y el grafo primero: el
    checkpointer indexa por thread_id, no por grafo."""
    if grafo not in GRAFOS:
        raise ValueError(f"grafo desconocido: {grafo}")
    if ":" not in sujeto:
        raise ValueError("el sujeto va con su clase delante")
    return f"{grafo}|{sujeto}"


def memoria(sujeto: str) -> tuple[str, str]:
    """La asimetría entera: el namespace del Store se teclea SOLO
    con el sujeto --- el checkpointer separa, el Store une."""
    clase, _, valor = sujeto.partition(":")
    return (clase, valor)          # ("cliente", "C-99"), del 6.2


# 12.5 servidor.py --- sustituye a `f"cliente:{cliente_id}"`.
HILO = hilo("conciliacion", f"cliente:{cliente_id}")

# 12.6 webhook_slack.py --- sustituye a `f"slack:{canal}:{ts}"`,
# que identifica una conversación, no a una persona. `cliente_de`
# es la tabla de dos columnas que escribes al abrir el hilo.
HILO = hilo("conciliacion", f"cliente:{cliente_de(ev)}")

# 13.4 --- aquí no hay línea que sustituir: hay dos que faltan,
# porque `construir_cerebro()` compila SIN checkpointer y el
# adaptador va sin `config`, y así la llamada no recuerda nada:
#   grafo_voz.py    create_agent(..., checkpointer=SAVER)
#   agente_voz.py   langchain.LLMAdapter(graph=..., config={
#                       "configurable": {"thread_id": HILO}})
# Y el sujeto sale del paso de identificación que voz no tiene
# todavía: `ctx.room.name` es una sala, no un cliente.

# 14.2 cara.py --- el avatar NO abre hilo: comparte la sesión del
# 13.4. Si abre uno, la misma persona tiene dos memorias.

# 11.5 batch_nocturno.py --- sustituye a `f"inc-{ref}"`: aquí el
# sujeto es la clave de negocio, de donde sale la idempotencia.
HILO = hilo("conciliacion", f"incidencia:{ref}")
