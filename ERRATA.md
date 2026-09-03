# Erratas y actualizaciones

*Ingeniería de Sistemas Agénticos* · primera edición, septiembre de 2026

El libro cierra su contenido en agosto de 2026 y lo dice en la página legal. Este fichero es la otra mitad de esa respuesta, y el 0.4 lo anuncia con su contrato: **cada corrección va fechada y dice qué versión de qué librería la provocó.** Antes de dar por roto un bloque de código del manual, mira aquí.

## Cómo leer este fichero

Una entrada por corrección, la más reciente primero. Cada una lleva:

- **Fecha** de publicación de la errata.
- **Dónde** — el apartado del libro y, si aplica, el fichero de `banco-meridiano/`.
- **Qué cambió fuera** — la versión de la librería, el endpoint, la norma o el precio que dejó de ser válido, con su número.
- **Qué hay que hacer** — el cambio concreto en el código o en la lectura.

Lo que **no** entra aquí: mejoras de estilo, ejercicios nuevos ni ampliaciones. Solo lo que hace que algo del libro haya dejado de ser cierto o de funcionar.

## Erratas

Ninguna todavía. Esta es la primera edición y se publica con el contenido cerrado en agosto de 2026; las entradas aparecerán debajo a medida que las versiones se muevan.

## Puntos abiertos que el libro ya declara

No son erratas: son restricciones que el manual reconoce en el 0.4 y en el A·J.6, y están aquí porque son los primeros sitios donde va a aparecer una errata.

**Tres librerías sin versión fijada.** El 0.4 ancla `langchain` 1.3.18, `langgraph` 1.2.11, `langchain-mcp-adapters` 0.3.2, `livekit-agents` 1.7.1 y `pgvector` 0.8.0 o superior. No fija `langchain-postgres`, `psycopg` ni `mcp`, porque no tenía una versión comprobada de las tres — la del primero es uno de los cuatro datos que el A·J.6 declara sin fuente. Toda la restricción efectiva ahí es el techo `mcp<2`, y el motivo está en el 10.2: en la rama 2.x, `FastMCP` pasa a ser `MCPServer`. Si algo del M7, del M10 o del checkpointer del M5 falla, es el primer sitio donde mirar.

**El techo `mcp<2`.** Cuando la rama 2.x se estabilice, el servidor del 10.1 y el cliente del 10.2 cambian de nombre de clase. Será la primera errata de este fichero.

**El transporte HTTP+SSE de MCP está deprecado, no retirado.** El M10 lo dice así a propósito: la política de ciclo de vida de la revisión 2026-07-28 define Active, Deprecated y Removed con una ventana mínima de doce meses. El día que pase a Removed, este fichero lo dirá con la fecha.

**El AI Act se aplica por tramos.** El M16 fecha las obligaciones que cita, incluidas las que el Digital Omnibus (Reglamento 2026/1744) movió. Los tramos que venzan después de agosto de 2026 se anotan aquí cuando entren en vigor, no cuando se anuncien.

**Los precios de la tabla del 15.5** — recargo de escritura de caché, lectura, batch — son los de agosto de 2026 y son lo primero que caduca de todo el libro. El J.7, si llega, será su sitio; hasta entonces, aquí.

## Versiones de referencia de esta edición

Es la tabla del 0.4, para tenerla sin abrir el libro. `banco-meridiano/pyproject.toml` las declara y es la fuente ejecutable.

| Librería | Versión | Qué depende de ella |
|---|---|---|
| `langchain` | 1.3.18 | `create_agent` y el orden del pipeline de middleware (4.2) |
| `langgraph` | 1.2.11 | el `interrupt` durable (6.1), `stream_mode="custom"` (6.3), la fábrica de `AsyncPostgresSaver` (5.3) |
| `langchain-mcp-adapters` | 0.3.2 | el cliente del 10.2, con el techo `mcp<2` |
| `livekit-agents` | 1.7.1 | `replace_audio_tail` (14.2) y el `SpeechHandle` del aviso del Art. 50 (16.5) |
| `pgvector` | 0.8.0 o superior | `hnsw.iterative_scan` (7.6, 8.1) |

## Cómo avisar de una errata

Abre una *issue* con el apartado del libro, lo que hiciste, lo que esperabas y lo que salió, y la versión de la librería que tienes instalada (`pip freeze | grep -E 'langchain|langgraph|mcp|livekit|psycopg'`). Sin la versión no se puede fechar la corrección, que es lo que este fichero promete.
