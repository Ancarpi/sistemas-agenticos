-- src/core/memoria.sql --- lo que le falta al schema.sql del 7.6
-- para que la memoria del 34.1 se pueda gobernar y borrar.
-- Requiere el DDL de banco.aprobaciones del 35.6 ya aplicado:
-- los ALTER del final la tocan. Reaplicable:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f src/core/memoria.sql
SET search_path = banco, public;

-- Los siete tipos del 34.1, con su TTL y su dueño. `dias` en
-- NULL es «no caduca por tiempo», y solo lo llevan los dos que
-- versiona un PR.
CREATE TABLE IF NOT EXISTS ttl_memoria (
    tipo  text PRIMARY KEY,
    dias  integer CHECK (dias IS NULL OR dias > 0),
    dueno text NOT NULL
);
INSERT INTO ttl_memoria (tipo, dias, dueno) VALUES
    ('working',       1, 'Plataforma'),
    ('thread',       90, 'Soporte'),
    ('individual',  365, 'DPO'),
    ('domain',      540, 'Steward de dominio'),
    ('collective',  730, 'Steward de dominio'),
    ('procedural', NULL, 'Plataforma'),
    ('episodic',   NULL, 'Cumplimiento')
ON CONFLICT (tipo) DO NOTHING;

-- El `MemoryRecord` del 34.2, que allí es un modelo Pydantic sin
-- tabla debajo. El namespace es el `(tenant, proposito, sujeto)`
-- del 37.2, y `sujeto` se repite en su columna porque una
-- supresión busca por sujeto y no por prefijo.
CREATE TABLE IF NOT EXISTS memoria (
    id            bigserial PRIMARY KEY,
    tipo          text   NOT NULL REFERENCES ttl_memoria(tipo),
    namespace     text[] NOT NULL,
    clave         text   NOT NULL,
    valor         jsonb  NOT NULL,
    sujeto        text,            -- el ID del 34.6, no el valor
    sensibilidad  text   NOT NULL DEFAULT 'internal',
    confianza     real   NOT NULL DEFAULT 1.0,
    consent_basis text,
    owner         text   NOT NULL,
    source_run_id text   NOT NULL,
    evidencia     text   NOT NULL,
    aprobado_por  text,
    propuesta_id  bigint,          -- la fila del 35.6 que publicó
    creado_en     timestamptz NOT NULL DEFAULT now(),
    expira_en     timestamptz,
    CONSTRAINT sensibilidad_valida CHECK (sensibilidad IN (
        'public', 'internal', 'confidential', 'restricted')),
    CONSTRAINT confianza_valida CHECK (
        confianza > 0 AND confianza <= 1),
    -- La sexta regla del arquitecto, en la base.
    CONSTRAINT memoria_gobernada CHECK (
        source_run_id <> ''
        AND (expira_en IS NOT NULL
             OR tipo IN ('procedural', 'episodic'))),
    -- El aprendizaje controlado del 34.3, también en la base.
    CONSTRAINT colectiva_aprobada CHECK (
        tipo NOT IN ('domain', 'collective')
        OR (aprobado_por IS NOT NULL
            AND propuesta_id IS NOT NULL)),
    -- Y el permiso, cobrado.
    CONSTRAINT individual_con_base CHECK (
        tipo <> 'individual' OR consent_basis IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS memoria_una_clave
    ON memoria (namespace, clave);
CREATE INDEX IF NOT EXISTS memoria_por_sujeto
    ON memoria (sujeto) WHERE sujeto IS NOT NULL;
CREATE INDEX IF NOT EXISTS memoria_caducidad
    ON memoria (expira_en) WHERE expira_en IS NOT NULL;

-- La caducidad efectiva. Un tipo con `dias` en NULL devuelve
-- NULL, y el CHECK de arriba es el que decide si eso vale.
CREATE OR REPLACE FUNCTION caduca_memoria(
    p_tipo text, p_creado timestamptz)
RETURNS timestamptz LANGUAGE sql STABLE AS $$
    SELECT p_creado + make_interval(days =>
        (SELECT dias FROM ttl_memoria WHERE tipo = p_tipo));
$$;
