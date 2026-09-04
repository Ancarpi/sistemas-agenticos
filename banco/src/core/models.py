# fábrica de modelos: el ÚNICO sitio del proyecto donde se instancia un LLM
import os
from langchain.chat_models import init_chat_model

def get_model(alias: str = "agente-rapido", **kwargs):
    """alias = un modelo de tu config de LiteLLM: 'agente-rapido'
    apunta a un modelo pequeño; 'agente-listo', a uno grande."""
    return init_chat_model(
        f"openai:{alias}",          # protocolo OpenAI-compatible
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
        **kwargs,
    )

def get_embeddings(alias: str = "emb-multilingue"):
    """Mismo principio para embeddings: el código solo conoce el gateway."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=alias,
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
        check_embedding_ctx_length=False,  # el proxy no es OpenAI
    )
