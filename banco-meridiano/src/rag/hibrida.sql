-- src/rag/hibrida.sql --- las dos ramas, en UN viaje a la base.
-- Va DENTRO de la transacción del 7.6: el rol agente_lectura y
-- meridiano.niveles ya están puestos, así que la política de RLS
-- es un tercer filtro de esta consulta que no aparece escrito en
-- ninguna de sus líneas.
WITH densa AS (
  -- El ROW_NUMBER va FUERA del LIMIT a propósito: dentro de la
  -- misma consulta, la función de ventana obliga a ordenar TODAS
  -- las filas que casan y el LIMIT deja de empujarse al índice.
  -- El resultado sale igual de correcto y cien veces más lento.
  SELECT langchain_id, ROW_NUMBER() OVER (ORDER BY dist) AS rango
  FROM (
    SELECT langchain_id, embedding <=> %(vec)s::vector AS dist
    FROM meridiano.manuales_meridiano
    -- Columnas tipadas del 7.6, no langchain_metadata. El
    -- «IS NULL OR» hace opcional cada filtro sin partir la
    -- consulta en dos, y con el parámetro ya sustituido el
    -- planificador se queda con manuales_filtros.
    WHERE (%(tipo)s::text IS NULL OR tipo = %(tipo)s)
      AND (%(producto)s::text IS NULL OR producto = %(producto)s)
    ORDER BY dist                    -- aquí manda el HNSW del 7.6
    LIMIT %(n_rama)s
  ) cabeza_densa
), consulta AS (
  -- plainto_tsquery une los términos con AND: «¿qué comisión
  -- aplica a la REF-4471?» exige que el trozo contenga TODAS las
  -- palabras, y no lo hace ninguno. Ahí es donde la rama léxica
  -- devuelve cero filas y el equipo concluye que «el híbrido no
  -- aporta». Se cambian los & por | y se vuelve a castear. Vale
  -- para lenguaje natural: si tu corpus mete URLs, el parser las
  -- emite como un lexema entero, con su & dentro, y el replace lo
  -- parte en dos --- ahí toca armar el OR lexema a lexema con
  -- ts_lexize en vez de a golpe de replace.
  SELECT CASE WHEN t = '' THEN NULL
              ELSE replace(t, '&', '|')::tsquery END AS q
  FROM (SELECT plainto_tsquery('es_meridiano',
                               %(texto)s)::text AS t) bruta
), lexica AS (
  SELECT langchain_id,
         ROW_NUMBER() OVER (ORDER BY peso DESC) AS rango
  FROM (
    SELECT m.langchain_id, ts_rank_cd(m.tsv, c.q) AS peso
    FROM meridiano.manuales_meridiano m, consulta c
    WHERE m.tsv @@ c.q
      AND (%(tipo)s::text IS NULL OR m.tipo = %(tipo)s)
      AND (%(producto)s::text IS NULL OR m.producto = %(producto)s)
    ORDER BY peso DESC
    LIMIT %(n_rama)s
  ) cabeza_lexica
)
SELECT langchain_id, d.rango AS r_densa, l.rango AS r_lexica
FROM densa d FULL OUTER JOIN lexica l USING (langchain_id);
