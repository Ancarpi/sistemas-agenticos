-- schema.sql --- de una vez y reaplicable:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f schema.sql

CREATE EXTENSION IF NOT EXISTS vector;      -- pgvector 0.8.0+
CREATE SCHEMA IF NOT EXISTS banco;
SET search_path = banco, public;

-- La 7.4 creó la tabla en public con sus cuatro columnas, no con
-- estas: moverla dejaría el CREATE de abajo en un no-op y el
-- índice de filtros moriría con «column "tipo" does not exist».
-- Se borra y no se pierde nada: el corpus hay que reindexarlo
-- igual con el schema_name y el metadata_columns nuevos.
DROP TABLE IF EXISTS public.manuales;

-- Las tres primeras columnas las nombra PGVectorStore: o se las
-- renombras también a create_sync(), o falla al arrancar.
CREATE TABLE IF NOT EXISTS manuales (
    langchain_id  uuid         PRIMARY KEY,
    content       text         NOT NULL,
    embedding     vector(1024) NOT NULL,
    -- Metadatos TIPADOS: los filtros del 7.4 y del Ej. 7.2.
    fuente        text         NOT NULL,
    seccion       text,
    producto      text,
    tipo          text         NOT NULL,
    version       integer      NOT NULL DEFAULT 1,
    clasificacion text         NOT NULL DEFAULT 'interna',
    fecha         date         NOT NULL,
    langchain_metadata json,   -- el cajón de sastre
    CONSTRAINT tipo_valido CHECK (
        tipo IN ('producto', 'normativa')),
    CONSTRAINT clasificacion_valida CHECK (
        clasificacion IN ('publica', 'interna', 'restringida'))
);
-- Coseno, porque PGVectorStore usa coseno por defecto. Un índice
-- con vector_l2_ops NO lo usa el operador <=>: no hay error, hay
-- escaneo secuencial. Se comprueba con EXPLAIN.
SET maintenance_work_mem = '512MB';
CREATE INDEX IF NOT EXISTS manuales_embedding_hnsw
    ON manuales
 USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
RESET maintenance_work_mem;

-- HNSW no ayuda con un WHERE. Los filtros quieren su propio índice.
CREATE INDEX IF NOT EXISTS manuales_filtros
    ON manuales (tipo, producto, version);
-- mod-97 (ISO 13616) en SQL. IMMUTABLE para usarla en un CHECK.
-- El CASE no es adorno: Postgres no garantiza el orden de un AND,
-- y sin él un IBAN con espacios revienta en el ::numeric.
CREATE OR REPLACE FUNCTION iban_es_valido(v text)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN v ~ '^ES[0-9]{22}$' THEN
        mod((substr(v, 5) || '1428' || substr(v, 3, 2))::numeric,
            97) = 1
    ELSE false END;
$$;

CREATE TABLE IF NOT EXISTS cuentas (
    iban       text   PRIMARY KEY,
    cliente_id text   NOT NULL,
    tipo       text   NOT NULL,
    saldo_cent bigint NOT NULL DEFAULT 0,
    CONSTRAINT iban_valido CHECK (iban_es_valido(iban))
);

CREATE TABLE IF NOT EXISTS transferencias (
    referencia     text PRIMARY KEY,
    iban_ordenante text NOT NULL REFERENCES cuentas(iban),
    beneficiario   text NOT NULL,
    importe_cent   bigint NOT NULL,
    concepto       text NOT NULL,
    creada_en      timestamptz NOT NULL,
    CONSTRAINT ref_formato CHECK (referencia ~ '^REF-[0-9]{4}$'),
    CONSTRAINT importe_positivo CHECK (importe_cent > 0),
    CONSTRAINT ben_valido CHECK (iban_es_valido(beneficiario))
);

CREATE TABLE IF NOT EXISTS incidencias (
    id         bigserial PRIMARY KEY,
    referencia text NOT NULL REFERENCES transferencias(referencia),
    estado     text NOT NULL DEFAULT 'abierta',
    motivo     text,
    resumen    text,
    cola       text,
    abierta_en timestamptz NOT NULL DEFAULT now(),
    cerrada_en timestamptz,
    CONSTRAINT estado_valido CHECK (
        estado IN ('abierta', 'escalada', 'resuelta')),
    CONSTRAINT cierre_coherente CHECK (
        (cerrada_en IS NOT NULL) = (estado = 'resuelta'))
);

-- La idempotencia del lote nocturno (11.3), en una línea de DDL:
-- el batch se reejecuta y no abre dos veces el mismo caso.
CREATE UNIQUE INDEX IF NOT EXISTS incidencias_una_viva
    ON incidencias (referencia) WHERE estado <> 'resuelta';
-- CREATE ROLE no admite IF NOT EXISTS; de ahí el rodeo.
DO $do$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='agente_lectura')
    THEN CREATE ROLE agente_lectura NOLOGIN; END IF; END $do$;
GRANT USAGE ON SCHEMA banco TO agente_lectura;
GRANT SELECT ON manuales TO agente_lectura;
GRANT agente_lectura TO CURRENT_USER;   -- si no, nadie se lo pone

ALTER TABLE manuales ENABLE ROW LEVEL SECURITY;
-- Sin FORCE, el DUEÑO se salta su propia política. Y tu
-- aplicación se conecta como dueño: sin esta línea RLS está
-- activada y no filtra nada, el peor de los dos estados.
ALTER TABLE manuales FORCE ROW LEVEL SECURITY;

-- Con FORCE y una sola política FOR SELECT, Postgres deniega el
-- resto por defecto y ni el dueño puede indexar: de ahí la de
-- ingesta. CREATE POLICY tampoco admite IF NOT EXISTS.
DROP POLICY IF EXISTS manuales_ingesta ON manuales;
CREATE POLICY manuales_ingesta ON manuales
    FOR ALL TO CURRENT_USER USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS manuales_por_nivel ON manuales;
CREATE POLICY manuales_por_nivel ON manuales
    FOR SELECT USING (
        clasificacion = ANY (string_to_array(
            coalesce(current_setting('banco.niveles', true),
                     'publica'), ',')));


-- --- anadido del M16.6 (extraer_meridiano) ---
-- registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6.
-- registro_ia --- Art. 12. Va en el schema.sql del 7.6.
CREATE TABLE IF NOT EXISTS registro_ia (
    id      bigserial   PRIMARY KEY,
    ts      timestamptz NOT NULL DEFAULT now(),
    tipo    text        NOT NULL,
    canal   text        NOT NULL,
    sujeto  text        NOT NULL,  -- id de cliente o de sala
    traza   text,                  -- el trace_id del M15, si hay
    detalle jsonb       NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT canal_valido CHECK (canal IN (
        'chat', 'slack', 'voz', 'avatar', 'backend')),
    CONSTRAINT tipo_valido CHECK (tipo IN (
        'art50_aviso', 'art14_aprobacion', 'art26_decision'))
);
CREATE INDEX IF NOT EXISTS registro_por_sujeto
    ON registro_ia (sujeto, ts DESC);

-- «Solo añadir» es el FORCE del 7.6 otra vez,
-- y hay que contar exactamente lo que hace. Con la RLS forzada y
-- políticas solo de INSERT y de SELECT, las filas dejan de
-- existir para UPDATE y DELETE: los dos se ejecutan SIN error y
-- afectan a cero filas, también al dueño de la tabla.
ALTER TABLE registro_ia ENABLE ROW LEVEL SECURITY;
ALTER TABLE registro_ia FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS registro_alta ON registro_ia;
CREATE POLICY registro_alta ON registro_ia
    FOR INSERT WITH CHECK (true);
DROP POLICY IF EXISTS registro_lectura ON registro_ia;
CREATE POLICY registro_lectura ON registro_ia
    FOR SELECT USING (true);

-- Y todo lo de arriba vale cero si la aplicación se conecta como
-- superusuario o con BYPASSRLS: los dos se saltan la RLS entera,
-- y son el DATABASE_URL por defecto de casi cualquier portátil.
-- Y CREATE ROLE no admite IF NOT EXISTS: el mismo rodeo que
-- agente_lectura en el 7.6, o la segunda pasada del fichero
-- aborta con «role already exists».
DO $do$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='banco_app')
    THEN CREATE ROLE banco_app LOGIN NOSUPERUSER NOBYPASSRLS;
  END IF; END $do$;
GRANT INSERT, SELECT ON registro_ia TO banco_app;
GRANT USAGE, SELECT ON SEQUENCE registro_ia_id_seq
    TO banco_app;
