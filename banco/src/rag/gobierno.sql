-- src/rag/gobierno.sql --- lo que le falta al schema.sql del 7.6
-- para que el corpus se pueda gobernar. Reaplicable:
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f src/rag/gobierno.sql
SET search_path = banco, public;

-- FRESCURA. `fecha` (7.6) es la del documento; `indexado_en` es
-- cuándo entró ESTE trozo al índice, y hacen falta las dos: un
-- manual de 2019 reindexado ayer es nuevo en el índice y viejo
-- en la realidad, y con una sola fecha los dos casos son uno.
ALTER TABLE manuales
  ADD COLUMN IF NOT EXISTS indexado_en timestamptz NOT NULL
      DEFAULT now(),
  ADD COLUMN IF NOT EXISTS valid_from date NOT NULL
      DEFAULT current_date,
  ADD COLUMN IF NOT EXISTS valid_to date,
  -- PROCEDENCIA. Sin estas dos, «lo dice el manual» es una
  -- afirmación sin dueño: nadie firmó ese texto.
  ADD COLUMN IF NOT EXISTS aprobado_por text,
  ADD COLUMN IF NOT EXISTS aprobado_en date;

-- El TTL vive en una tabla y no en el código porque quien lo
-- firma (cumplimiento) no despliega. Los dos números son
-- política, no medición: cámbialos por los de tu banco.
CREATE TABLE IF NOT EXISTS ttl_corpus (
    tipo text PRIMARY KEY,
    dias integer NOT NULL CHECK (dias > 0),
    dueno text NOT NULL
);
INSERT INTO ttl_corpus (tipo, dias, dueno) VALUES
    ('producto',   180, 'Productos'),
    ('normativa', 1095, 'Cumplimiento')
ON CONFLICT (tipo) DO NOTHING;

-- Caducidad efectiva: la vigencia declarada del documento o el
-- TTL de su tipo, lo que llegue antes. LEAST ignora los NULL, y
-- eso es justo lo que se quiere: sin `valid_to` manda el TTL, y
-- sin fila en ttl_corpus manda `valid_to`.
CREATE OR REPLACE FUNCTION caduca_el(
    p_tipo text, p_indexado timestamptz, p_hasta date)
RETURNS date LANGUAGE sql STABLE AS $$
    SELECT least(p_hasta, (p_indexado + make_interval(days =>
        (SELECT dias FROM ttl_corpus WHERE tipo = p_tipo)))::date);
$$;

-- PERMISOS POR TROZO, la mitad que el 7.6 no cubre. Aquella
-- política filtra por clasificación; esta filtra por vigencia, y
-- va AS RESTRICTIVE porque dos políticas permisivas se combinan
-- con OR: la misma línea sin esas dos palabras AMPLÍA lo que se
-- ve en vez de recortarlo, y no da ningún error al hacerlo.
-- El TO acota la restricción al rol del retriever, para que la
-- ingesta y el inventario sigan viendo el corpus entero.
DROP POLICY IF EXISTS manuales_vigentes ON manuales;
CREATE POLICY manuales_vigentes AS RESTRICTIVE
    FOR SELECT TO agente_lectura USING (
        valid_from <= current_date
        AND coalesce(caduca_el(tipo, indexado_en, valid_to),
                     current_date) >= current_date);

-- Sin este GRANT la política falla por dentro y TODA búsqueda
-- muere con «permission denied for table ttl_corpus».
GRANT SELECT ON ttl_corpus TO agente_lectura;
CREATE INDEX IF NOT EXISTS manuales_vigencia
    ON manuales (valid_from, valid_to);
