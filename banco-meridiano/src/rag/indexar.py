from langchain_postgres import PGEngine, PGVectorStore

# la URL debe llevar driver explícito: postgresql+psycopg://...
engine = PGEngine.from_connection_string(
    url=os.environ["DATABASE_URL_SQLALCHEMY"])
engine.init_vectorstore_table(
    table_name="manuales_meridiano", vector_size=1024)

vectores = PGVectorStore.create_sync(
    engine=engine,
    table_name="manuales_meridiano",
    embedding_service=get_embeddings("emb-multilingue"),
)
vectores.add_documents(chunks)           # cada doc con su .metadata
hits = vectores.similarity_search("¿comisión por descubierto?",
                                  k=5, filter={"producto": "cuentas"})
