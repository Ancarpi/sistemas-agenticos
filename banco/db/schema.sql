-- db/schema.sql --- de una vez y reaplicable:
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


-- --- anadido del M16.6 (extraer_banco) ---
-- registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6.
-- registro_ia --- Art. 12. Va en el db/schema.sql del 7.6.
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
-- El mismo GRANT USAGE que agente_lectura en el 7.6, y por lo
-- mismo: la tabla vive en el esquema banco, y sin permiso
-- sobre el ESQUEMA el primer INSERT muere con «permission
-- denied for schema banco». El rol que este apartado exige
-- usar no podría escribir ni una fila del Art. 12.
GRANT USAGE ON SCHEMA banco TO banco_app;
-- Los cuatro verbos, porque el «sin error y cero filas» de arriba
-- solo se puede observar con un rol que TENGA el UPDATE y el DELETE.
-- Sin ellos lo que sale es «permission denied», otro mecanismo y otra
-- lección. El test del 16.7 se conecta con este rol.
GRANT INSERT, SELECT, UPDATE, DELETE ON registro_ia TO banco_app;
GRANT USAGE, SELECT ON SEQUENCE registro_ia_id_seq
    TO banco_app;


-- --- anadido del M21.5 (extraer_banco) ---
-- banco.trabajos y banco.efectos (cola con leases y libro mayor de la saga). El libro dice literalmente que van al final del db/schema.sql del 7.6.
-- Al final de db/schema.sql (7.6): banco.trabajos es la cola y
-- banco.efectos el libro mayor de la saga.
CREATE TABLE IF NOT EXISTS banco.trabajos (
    id          bigserial PRIMARY KEY,
    tipo        text  NOT NULL,     -- 'triaje', 'devolucion', ...
    clave       text  NOT NULL,     -- la clave de NEGOCIO
    carga       jsonb NOT NULL,
    estado      text  NOT NULL DEFAULT 'pending',
    prioridad   int   NOT NULL DEFAULT 0,
    intentos    int   NOT NULL DEFAULT 0,
    worker      text,
    lease_hasta timestamptz,
    correr_tras timestamptz NOT NULL DEFAULT now(),
    error       text,
    resultado   jsonb,
    creado_en   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT estado_trabajo CHECK (estado IN ('pending',
        'leased', 'running', 'waiting_human', 'retry_scheduled',
        'completed', 'dead_letter'))
);

-- El índice único parcial del 7.6, ahora en la cola: el mismo
-- caso no se encola dos veces mientras siga vivo.
CREATE UNIQUE INDEX IF NOT EXISTS trabajos_uno_vivo
    ON banco.trabajos (tipo, clave)
 WHERE estado NOT IN ('completed', 'dead_letter');

-- Sin este, cada reclamo recorre la cola entera, cerrados
-- incluidos, y la cola solo crece.
CREATE INDEX IF NOT EXISTS trabajos_reclamables
    ON banco.trabajos (prioridad DESC, creado_en)
 WHERE estado IN ('pending', 'retry_scheduled', 'leased',
                  'running');   -- la misma lista que el RECLAMO

CREATE TABLE IF NOT EXISTS banco.efectos (
    id            bigserial PRIMARY KEY,
    trabajo_id    bigint NOT NULL REFERENCES banco.trabajos(id),
    paso          text   NOT NULL,
    datos         jsonb  NOT NULL,
    aplicado_en   timestamptz NOT NULL DEFAULT now(),
    compensado_en timestamptz
);


-- --- anadido del M35.6 (extraer_banco) ---
-- banco.aprobaciones (la cola de aprobaciones con su receipt firmado). El libro dice literalmente que va al final del db/schema.sql del 7.6, junto a banco.trabajos.
-- Al final de db/schema.sql (7.6), junto a banco.trabajos (21.5):
-- la cola de aprobaciones. Una fila por PROPUESTA, y el receipt
-- firmado en la misma fila, porque una decisión sin su propuesta
-- delante no se audita.
CREATE TABLE IF NOT EXISTS banco.aprobaciones (
    id          bigserial PRIMARY KEY,
    hilo        text  NOT NULL,      -- el thread_id del 18.3
    huella      text  NOT NULL,      -- sha256(accion + propuesta)
    run_id      text  NOT NULL,      -- el run que PROPUSO
    agente      text  NOT NULL,
    version     text  NOT NULL,
    accion      text  NOT NULL,      -- el nombre del catálogo
    propuesta   jsonb NOT NULL,      -- los `args` del modelo
    propone     text  NOT NULL,      -- el humano que delegó (35.3)
    estado      text  NOT NULL DEFAULT 'pendiente',
    aprobador   text,
    decidido_en timestamptz,
    diff        jsonb,
    motivo      text,
    firma       text,
    creado_en   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT estado_aprobacion CHECK (estado IN ('pendiente',
        'aprobada', 'editada', 'rechazada', 'caducada')),
    -- Ninguna fila decidida sin firma y ninguna pendiente con
    -- firma: el CHECK es lo que impide el receipt a medias.
    CONSTRAINT firmada_si_decidida CHECK (
        (estado = 'pendiente') = (firma IS NULL)),
    CONSTRAINT firmante_si_decidida CHECK (
        (estado = 'pendiente') = (aprobador IS NULL)),
    -- Maker-checker en la base, no solo en Python: el día que
    -- alguien apruebe desde una consola SQL, la fila se rechaza.
    CONSTRAINT sin_autoaprobacion CHECK (
        estado <> 'aprobada' AND estado <> 'editada'
        OR aprobador <> propone)
);

-- El índice parcial del 21.5, aquí. Cubre la carrera: dos workers
-- que reclamen la misma propuesta a la vez. Lo que NO cubre es la
-- reanudación, porque para entonces la fila está `aprobada` y un
-- índice parcial sobre `pendiente` no la ve: de eso se encarga el
-- SELECT de `encolar`, que mira las vivas: pendiente, aprobada y
-- editada. Una rechazada o caducada no bloquea la siguiente.
CREATE UNIQUE INDEX IF NOT EXISTS aprobaciones_una_viva
    ON banco.aprobaciones (hilo, huella)
 WHERE estado = 'pendiente';

-- La pantalla pide siempre lo mismo, y ordenado por antigüedad.
CREATE INDEX IF NOT EXISTS aprobaciones_pendientes
    ON banco.aprobaciones (creado_en)
 WHERE estado = 'pendiente';


-- --- anadido del M34.7 (extraer_banco) ---
-- banco.supresiones y los cuatro ALTER de la supresion RGPD (aprobaciones, manuales, registro_ia). Va detras de aprobaciones: sus ALTER la necesitan creada.
-- El hecho sin el dato dentro (34.6): una fila por SOLICITUD y
-- por almacén. No lleva valores ni texto libre, solo el
-- identificador del sujeto, el almacén, la acción y cuántas
-- filas cayeron. Es la tabla que se le enseña a un DPO.
CREATE TABLE IF NOT EXISTS supresiones (
    id            bigserial PRIMARY KEY,
    solicitud     text NOT NULL,   -- el expediente del DPO
    sujeto        text NOT NULL,   -- el id, jamás el nombre
    almacen       text NOT NULL,
    tablas        text[] NOT NULL,
    accion        text NOT NULL,
    filas         integer NOT NULL DEFAULT 0,
    dueno         text NOT NULL,
    plazo_dias    integer,
    base          text,            -- por qué se conserva
    ejecutado_por text NOT NULL,
    ts            timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT accion_valida CHECK (accion IN ('borrado',
        'redactado', 'conservado', 'delegado', 'bloqueado')),
    -- Lo que se conserva o se delega lleva escrita su base, y lo
    -- que se borra no la necesita.
    CONSTRAINT base_si_se_queda CHECK (
        base IS NOT NULL
        OR accion NOT IN ('conservado', 'delegado'))
);
-- Reejecutar el mismo expediente actualiza su fila en vez de
-- abrir una segunda: una solicitud de supresión se repite todos
-- los días, y el criterio del Ejercicio 34.3 es que no reviente.
CREATE UNIQUE INDEX IF NOT EXISTS supresiones_una_por_almacen
    ON supresiones (solicitud, almacen);

-- El receipt del 35.6 es inmutable por diseño y aun así lleva la
-- propuesta dentro, y una propuesta lleva lo que el modelo
-- escribió. Se le añade la marca de purga: se va el CONTENIDO
-- (`propuesta` y `diff`), se queda el HECHO (quién firmó, cuándo
-- y con qué firma). `propuesta` es NOT NULL allí, así que la
-- purga escribe `{}` y no NULL.
--
-- Y la columna que hace posible encontrar las filas de una
-- persona: el `hilo` del 18.3 lleva el CASO y no al sujeto, así
-- que una supresión sin ella es un LIKE que no acierta. La
-- rellena el `encolar` del 35.6, que gana un kwarg y nada más.
ALTER TABLE aprobaciones
  ADD COLUMN IF NOT EXISTS purgado_en timestamptz,
  ADD COLUMN IF NOT EXISTS purgado_por text,
  ADD COLUMN IF NOT EXISTS sujeto text;
CREATE INDEX IF NOT EXISTS aprobaciones_sujeto
    ON aprobaciones (sujeto) WHERE sujeto IS NOT NULL;

-- El cuarto hábito del 34.6 hecho columna: el documento con dato
-- personal se marca al indexarlo. Sin ella, la supresión en el
-- corpus es un LIKE sobre `content` que no encuentra al cliente
-- cuyo nombre quedó partido entre dos trozos.
ALTER TABLE manuales
  ADD COLUMN IF NOT EXISTS sujeto text;
CREATE INDEX IF NOT EXISTS manuales_sujeto
    ON manuales (sujeto) WHERE sujeto IS NOT NULL;

-- El registro del 16.6 admite tres tipos, y una supresión del
-- RGPD es un cuarto hecho que hay que poder enseñar en la misma
-- consulta. Un CHECK no se amplía: se sustituye.
ALTER TABLE registro_ia DROP CONSTRAINT IF EXISTS tipo_valido;
ALTER TABLE registro_ia ADD CONSTRAINT tipo_valido CHECK (
    tipo IN ('art50_aviso', 'art14_aprobacion',
             'art26_decision', 'rgpd_supresion'));
