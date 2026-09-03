# Sin gateway no hay alias: los resuelves tú, en la fábrica.
# El resto del libro no se entera --- ese era el objetivo del 0.4.
ALIAS_DIRECTO = {
    "agente-rapido": "gpt-5-mini",
    "agente-rapido-2": "gpt-5-mini",
    "agente-equilibrado": "gpt-5",
    "agente-listo": "gpt-5",
    "agente-listo-backup": "gpt-5",
    "emb-multilingue": "text-embedding-3-large",  # ¡3072 dims!
}

def get_model(alias: str = "agente-rapido", **kwargs):
    modelo = ALIAS_DIRECTO.get(alias, alias)
    return init_chat_model(
        f"openai:{modelo}",
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
        **kwargs,
    )

# get_embeddings resuelve su alias con el mismo diccionario.
