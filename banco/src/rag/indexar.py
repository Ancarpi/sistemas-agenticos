import os

from langchain_postgres import PGEngine, PGVectorStore

from src.core.models import get_embeddings   # la fábrica del 0.4
from src.rag.trocear import documentos, trocear   # el 7.3

# la URL debe llevar driver explícito: postgresql+psycopg://...
engine = PGEngine.from_connection_string(
    url=os.environ["DATABASE_URL_SQLALCHEMY"])
engine.init_vectorstore_table(
    table_name="manuales", vector_size=1024)

vectores = PGVectorStore.create_sync(
    engine=engine,
    table_name="manuales",
    embedding_service=get_embeddings("emb-multilingue"),
)
trozos = trocear(texto, meta)            # dicts, no Document
vectores.add_documents(documentos(trozos))   # el puente del 7.3
hits = vectores.similarity_search("¿comisión por descubierto?",
                                  k=5, filter={"producto": "cuentas"})
