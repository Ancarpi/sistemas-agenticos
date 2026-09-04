# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**
se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 11223 lineas. 63 ficheros, 73 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `src/rag/trocear.py` | M7.3 | verbatim | L2054-2143 | Entregado del M7.3. |
| `src/channels/confianza.py` | M22.5 | verbatim | L6610-6697 | Entregado del M22.5. |
| `src/agents/handoff.py` | M23.5 | verbatim | L6943-7092 | Entregado del M23.5. |
| `src/rag/gobierno.sql` | M24.6 | verbatim | L7305-7367 | Entregado del M24.6. |
| `src/rag/gobierno.py` | M24.6 | verbatim | L7375-7497 | Entregado del M24.6. |
| `config/politica.yaml` | M26.2 | verbatim | L7741-7775 | Entregado del M26.2. |
| `src/ops/migrar_checkpoints.py` | M27.4 | verbatim | L8062-8193 | Entregado del M27.4. |
| `runbooks/deriva.py` | M28.5 | verbatim | L8436-8517 | Entregado del M28.5. |
| `src/finops/coste_por_resolucion.py` | M29.4 | verbatim | L8615-8798 | Entregado del M29.4. |
| `equipo.yaml` | M30.5 | verbatim | L8913-8968 | Entregado del M30.5. |
| `equipo.py` | M30.5 | verbatim | L8979-9068 | Entregado del M30.5. |
| `src/core/trabajos.py` | M21.5 | verbatim | L6286-6452 | Entregado del M21.5. |
| `src/core/politica.py` | M26.5 | verbatim | L7826-7910 | Entregado del M26.5. |
| `plataforma/estado.py` | M32.2 | verbatim | L9263-9296 | Un pool, un checkpointer y un store para toda la plataforma: el estado deja de ser de cada agente. |
| `plataforma/registro.py` | M32.3 | verbatim | L9351-9388 | El control plane resolviendo un id a paquete y fabrica. Sin publicacion no hay produccion. |
| `plataforma/catalogo.py` | M33.6 | verbatim | L9547-9612 | El resolutor del catalogo compartido: seleccion dinamica por contexto y permisos, con el sello que invalida la cache. |
| `plataforma/trazas.py` | M36.6 | verbatim | L10026-10088 | El esquema de traza del 36.1 como codigo: la unidad de observacion de una flota es la decision, no la CPU. |
| `gateway/config.yaml` | M0.5 | verbatim | L265-343 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L354-360 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L216-228 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L422-442 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L733-768 | El core bancario del 3.3 --- los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L722-798, L809-869, L877-950 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1018-1065 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1158-1163 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | Ej. 5.1 | plantilla | --- | Andamio del Ejercicio 5.1. El libro no publica este fichero y sin embargo lo importa en el 6.3 y en el 12.5. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.1 | patch | L1360-1379 | El estado y el grafo del 5.1: EstadoBackoffice, nodos y aristas. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1810-1824 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1764-1802 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1844-1913 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L2294-2327, L2335-2347, L2392-2441, L2455-2481 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L5232-5275 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `src/rag/indexar.py` | M7.4 | verbatim | L2259-2274 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: le falta el import os y de donde salen los chunks. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2556-2589 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2600-2651 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2662-2796 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L2857-2920 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L3053-3103, L3114-3152, L3163-3229, L3237-3346 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L3472-3535 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L3543-3587 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L3682-3788, L3796-3811 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L5598-5611 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L3924-4030 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L5467-5516 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L5574-5590 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L4062-4163 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L4243-4250 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L4315-4399 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L4501-4592 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L5099-5163 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L5292-5329 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L5333-5358 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L5426-5459 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L5530-5560 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L5730-5774 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L5872-5902 | El ContextContract y el contrato de triaje. Valida contra schemas/context-contract.schema.json. |
| `config/model_routing.yaml` | M19.2 | verbatim | L5924-5945 | Politica de routing por tarea, con presupuesto de pensamiento y de coste. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L6036-6067 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L6084-6113 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L6131-6150 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L6579-6594 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L6871-6885 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/politica.py` | M35.2 | patch | L9850-9858 | PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta. |
| `src/core/memoria.py` | M34.1 | verbatim | L9681-9696 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.5 | patch | L9737-9745 | PENDIENTE. Las tres APIs tipadas de memoria con sus receipts: los cuerpos son ... y los tres tipos de receipt no existen todavia, asi que el modulo no importa hasta que los escribas. |
| `src/evals/trayectoria.py` | M25.3 | verbatim | L7572-7594 | ExpectedTrajectory y assert_trajectory: se evalua el camino, no solo la respuesta. |
| `src/evals/medidas.py` | Ej. 31.1 | plantilla | --- | Andamio del Ejercicio 31.1: las seis medidas que aceptacion.py importa. El libro no las entrega, y lo dice. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L7610-7623 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L9126-9167 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L9313-9339 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L10149-10300, L10311-10384 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
