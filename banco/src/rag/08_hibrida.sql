-- src/rag/08_hibrida.sql --- el lado léxico, y solo el léxico.
-- Se ejecuta UNA vez sobre la tabla del 7.6, que ya no vive en
-- public: sin esta línea, manuales a secas ni siquiera
-- resuelve, porque el 7.6 la dejó en banco.
SET search_path = banco, public;

-- 1. La configuración 'spanish' de serie stemiza («comisiones» y
--    «comisión» son el mismo lexema) pero NO quita tildes, y el
--    cliente escribe «comision». Se encadena unaccent delante.
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE TEXT SEARCH CONFIGURATION es_banco (COPY = spanish);
ALTER TEXT SEARCH CONFIGURATION es_banco
  ALTER MAPPING FOR hword, hword_part, word
  WITH unaccent, spanish_stem;

-- 2. Columna generada + GIN. Es GENERATED porque to_tsvector con
--    configuración explícita es IMMUTABLE; to_tsvector(content) a
--    secas es STABLE y Postgres la RECHAZA aquí. Ese rechazo es lo
--    mejor que te puede pasar: es el único aviso de que ibas a
--    indexar en inglés, que es el default_text_search_config de
--    casi todo Postgres gestionado.
ALTER TABLE manuales
  ADD COLUMN tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('es_banco', content)) STORED;

CREATE INDEX manuales_tsv_gin ON manuales USING gin (tsv);

-- 3. Y aquí se acaba: lo demás ya está. Los filtros NO van contra
--    langchain_metadata --- que sigue siendo json, sin operador
--    @> y sin índice ---, sino contra las columnas tipadas y su
--    índice manuales_filtros. Y el lado denso es el HNSW de
--    coseno del 7.6, con su m y su ef_construction elegidos: un
--    segundo índice sobre la misma columna no acelera ninguna
--    consulta y encarece cada INSERT.
