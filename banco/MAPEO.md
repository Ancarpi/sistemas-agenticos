# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**
se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 13602 lineas. 72 ficheros, 91 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `src/core/memoria.sql` | M34.7 | verbatim | L10997-11087 | Entregado del M34.7. |
| `tests/test_registro.py` | M16.7 | verbatim | L5907-5933 | Entregado del M16.7. |
| `tests/test_art50.py` | M16.7 | verbatim | L5843-5879 | Entregado del M16.7. |
| `tests/test_art50.py` | M16.7 | patch | L5887-5903 | Anadido del M16.7. |
| `src/core/supresion.py` | M34.7 | verbatim | L11497-11691 | Entregado del M34.7. |
| `src/rag/responder.py` | M7.5 | verbatim | L2386-2482 | Entregado del M7.5. |
| `evals/run_rag_eval.py` | M8.3 | verbatim | L3205-3332 | Entregado del M8.3. |
| `src/core/hitl.py` | M35.6 | verbatim | L11946-12183 | Entregado del M35.6. |
| `src/core/router.py` | M19.6 | verbatim | L6580-6712 | Entregado del M19.6. |
| `src/core/catalogo_tools.py` | M20.6 | verbatim | L6980-7122 | Entregado del M20.6. |
| `src/evals/trayectoria.py` | M25.7 | verbatim | L8636-8708 | Entregado del M25.7. |
| `src/evals/trayectoria.py` | M25.7 | patch | L8716-8791 | Anadido del M25.7. |
| `src/rag/trocear.py` | M7.3 | verbatim | L2096-2318 | Entregado del M7.3. |
| `src/channels/confianza.py` | M22.5 | verbatim | L7598-7688 | Entregado del M22.5. |
| `src/agents/handoff.py` | M23.5 | verbatim | L7931-8080 | Entregado del M23.5. |
| `src/rag/gobierno.sql` | M24.6 | verbatim | L8293-8355 | Entregado del M24.6. |
| `src/rag/gobierno.py` | M24.6 | verbatim | L8363-8485 | Entregado del M24.6. |
| `config/politica.yaml` | M26.2 | verbatim | L8906-8952 | Entregado del M26.2. |
| `src/ops/migrar_checkpoints.py` | M27.4 | verbatim | L9245-9376 | Entregado del M27.4. |
| `runbooks/deriva.py` | M28.5 | verbatim | L9622-9711 | Entregado del M28.5. |
| `src/finops/coste_por_resolucion.py` | M29.4 | verbatim | L9809-9996 | Entregado del M29.4. |
| `equipo.yaml` | M30.5 | verbatim | L10111-10166 | Entregado del M30.5. |
| `equipo.py` | M30.5 | verbatim | L10177-10266 | Entregado del M30.5. |
| `src/core/trabajos.py` | M21.5 | verbatim | L7243-7439 | Entregado del M21.5. |
| `src/core/politica.py` | M26.5 | verbatim | L9003-9128 | Entregado del M26.5. |
| `plataforma/estado.py` | M32.2 | verbatim | L10461-10494 | Un pool, un checkpointer y un store para toda la plataforma: el estado deja de ser de cada agente. |
| `plataforma/registro.py` | M32.3 | verbatim | L10549-10592 | El control plane resolviendo un id a paquete y fabrica. Sin publicacion no hay produccion. |
| `plataforma/catalogo.py` | M33.6 | verbatim | L10751-10816 | El resolutor del catalogo compartido: seleccion dinamica por contexto y permisos, con el sello que invalida la cache. |
| `plataforma/trazas.py` | M36.6 | verbatim | L12374-12436 | El esquema de traza del 36.1 como codigo: la unidad de observacion de una flota es la decision, no la CPU. |
| `gateway/config.yaml` | M0.5 | verbatim | L289-367 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L378-384 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L237-263 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L446-466 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L763-798 | El core bancario del 3.3 --- los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L746-833, L844-904, L912-985 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1053-1100 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1193-1293 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.3 | verbatim | L1471-1693 | Entregado del M5.3. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.1 | patch | L1395-1414 | El estado y el grafo del 5.1: EstadoBackoffice, nodos y aristas. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1849-1863 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1803-1841 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1883-1955 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L2529-2562, L2570-2582, L2627-2676, L2690-2716 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L5707-5756 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `src/rag/indexar.py` | M7.4 | verbatim | L2350-2368 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: le falta el import os y de donde salen los chunks. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2791-2824 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2835-2886 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2897-3031 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L3092-3155 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L3475-3525, L3536-3574, L3585-3651, L3659-3768 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/agents/supervisor/supervisor.py` | M23.5 | patch | L8097-8165 | Anadido del M23.5. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L3894-3957 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L3965-4009 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L4104-4210, L4218-4233 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L6173-6186 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L4346-4452 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6042-6091 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6149-6165 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L4484-4585 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L4665-4729 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L4740-4824 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L4926-5017 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L5574-5638 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L5773-5810 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L5814-5839 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L6001-6034 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/despliegue-chat.yaml` | M27.2 | patch | L9200-9219 | Anadido del M27.2. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L6105-6135 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L6305-6349 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L6450-6480 | El ContextContract y el contrato de triaje. Valida contra schemas/context-contract.schema.json. |
| `config/model_routing.yaml` | M19.2 | verbatim | L6502-6523 | Politica de routing por tarea, con presupuesto de pensamiento y de coste. |
| `config/model_routing.yaml` | M19.6 | patch | L6720-6736 | Anadido del M19.6. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L6790-6839 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L6856-6902 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L6920-6945 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L7567-7582 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L7859-7873 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/politica.py` | M35.2 | patch | L11877-11885 | PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta. |
| `src/core/memoria.py` | M34.1 | verbatim | L10885-10900 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.5 | patch | L10941-10968 | PENDIENTE. Las tres APIs tipadas de memoria con sus receipts: los cuerpos son ... y los tres tipos de receipt no existen todavia, asi que el modulo no importa hasta que los escribas. |
| `src/core/memoria.py` | M34.7 | patch | L11167-11287 | Anadido del M34.7. |
| `src/core/memoria.py` | M34.7 | patch | L11291-11489 |  |
| `src/evals/medidas.py` | M15.7 | verbatim | L5192-5320 | Entregado del M15.7. |
| `src/evals/medidas.py` | M15.7 | patch | L5347-5419 | Anadido del M15.7. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L8598-8611 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L10324-10365 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L10511-10537 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L12497-12650, L12661-12770 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `plataforma/runtime.py` | M37.2 | patch | L12497-12650 | Anadido del M37.2. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
