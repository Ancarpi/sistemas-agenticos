# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_meridiano/extraer_meridiano.py`. No se edita a mano:**
se edita `tools/extraer_meridiano/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 8157 lineas. 48 ficheros, 58 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `gateway/config.yaml` | M0.5 | verbatim | L258-336 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L347-353 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L225-248 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L415-435 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L733-757 | El core bancario del 3.3 --- los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L723-787, L798-858, L866-939 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1007-1054 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1147-1247 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | Ej. 5.1 | plantilla | --- | Andamio del Ejercicio 5.1. El libro no publica este fichero y sin embargo lo importa en el 6.3 y en el 12.5. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.1 | patch | L1349-1368 | El estado y el grafo del 5.1: EstadoBackoffice, nodos y aristas. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1552-1565 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1511-1544 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1585-1654 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L1832-1863, L1871-1883, L1928-1977, L1991-2017 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L4555-4592 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `src/rag/indexar.py` | M7.4 | verbatim | L1797-1812 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: le falta el import os y de donde salen los chunks. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2092-2125 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2136-2187 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2198-2329 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L2390-2453 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L2586-2636, L2647-2685, L2696-2762, L2770-2872 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L2998-3061 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L3069-3113 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L3208-3314, L3322-3337 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L4913-4926 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L3450-3552 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L4784-4831 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L4889-4905 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L3584-3685 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L3765-3826 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L3837-3921 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L4023-4114 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L4423-4486 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L4609-4646 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L4650-4675 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L4743-4776 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L4845-4875 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L5045-5089 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L5187-5217 | El ContextContract y el contrato de triaje. Es Python, asi que no lo valida isa_validate: la version en datos es `contratos/triage_sepa.contract.yaml`. |
| `contratos/triage_sepa.contract.yaml` | M19.1 | traducido a datos | L5187-5217 | El mismo contrato de triaje como YAML. Valida contra schemas/context-contract.schema.json, que es el modo `context-contract` de isa_validate. |
| `evals/capstone_gate.eval.yaml` | M18.4 + M15.6 | plantilla | L5525-5545 | La puerta de release del capstone con los seis campos del 15.6. Valida contra schemas/eval-card.schema.json. Lleva 246 casos en `Recall@5`, no los 120 de la tabla: el propio 15.7 demuestra con `casos_para(0,05)` que 120 no sostiene una caida de cinco puntos. |
| `config/model_routing.yaml` | M19.2 | verbatim | L5239-5260 | Politica de routing por tarea, con presupuesto de pensamiento y de coste. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L5359-5390 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L5407-5436 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L5454-5473 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L5679-5694 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L5736-5750 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/trabajos.py` | M21.2 | verbatim | L5562-5577 | claim_next_job con lease y FOR UPDATE SKIP LOCKED. La maquina de estados del 21.2 es una tabla en prosa y se queda en el libro. |
| `src/core/politica.py` | M26.2 | verbatim | L6095-6124 | El policy engine fuera del modelo: ActionRequest, PolicyDecision y authorize_action. |
| `src/core/politica.py` | M35.2 | patch | L7076-7084 | PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta. |
| `src/core/memoria.py` | M34.1 | verbatim | L6907-6922 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.5 | patch | L6963-6990 | PENDIENTE. Las tres APIs tipadas de memoria con sus receipts: los cuerpos son ... y los tres tipos de receipt no existen todavia, asi que el modulo no importa hasta que los escribas. |
| `src/evals/trayectoria.py` | M25.3 | verbatim | L5966-5988 | ExpectedTrajectory y assert_trajectory: se evalua el camino, no solo la respuesta. |
| `src/evals/medidas.py` | Ej. 31.1 | plantilla | --- | Andamio del Ejercicio 31.1: las seis medidas que aceptacion.py importa. El libro no las entrega, y lo dice. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L6004-6017 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L6532-6587 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L6685-6711 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L7296-7333, L7344-7365 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
