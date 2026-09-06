# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**
se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 14145 lineas. 73 ficheros, 89 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `src/core/memoria.sql` | M34.7 | verbatim | L11304-11384 | Entregado del M34.7. |
| `tests/test_registro.py` | M16.7 | verbatim | L6000-6028 | Entregado del M16.7. |
| `tests/test_art50.py` | M16.7 | verbatim | L5980-5996 | Anadido del M16.7. |
| `src/core/supresion.py` | M34.7 | verbatim | L11819-11848, L11856-11918, L11926-11985, L11993-12050 | Entregado del M34.7. |
| `src/rag/responder.py` | M7.5 | verbatim | L2475-2571 | Entregado del M7.5. |
| `evals/run_rag_eval.py` | M8.3 | verbatim | L3293-3420 | Entregado del M8.3. |
| `src/core/hitl.py` | M35.6 | verbatim | L12272-12344, L12352-12438, L12446-12538, L12546-12613 | Entregado del M35.6. |
| `src/core/router.py` | M19.6 | verbatim | L6707-6851 | Entregado del M19.6. |
| `src/core/catalogo_tools.py` | M20.6 | verbatim | L7140-7282 | Entregado del M20.6. |
| `src/evals/trayectoria.py` | M25.7 | verbatim | L8854-8926 | Entregado del M25.7. |
| `src/evals/trayectoria.py` | M25.7 | patch | L8934-9009 | Anadido del M25.7. |
| `src/rag/trocear.py` | M7.3 | verbatim | L2176-2404 | Entregado del M7.3. |
| `src/channels/confianza.py` | M22.5 | verbatim | L7779-7869 | Entregado del M22.5. |
| `src/agents/handoff.py` | M23.5 | verbatim | L8112-8261 | Entregado del M23.5. |
| `src/rag/gobierno.sql` | M24.6 | verbatim | L8511-8573 | Entregado del M24.6. |
| `src/rag/gobierno.py` | M24.6 | verbatim | L8581-8703 | Entregado del M24.6. |
| `config/politica.yaml` | M26.2 | verbatim | L9124-9170 | Entregado del M26.2. |
| `src/ops/migrar_checkpoints.py` | M27.4 | verbatim | L9492-9629 | Entregado del M27.4. |
| `runbooks/deriva.py` | M28.5 | verbatim | L9875-9964 | Entregado del M28.5. |
| `src/finops/coste_por_resolucion.py` | M29.4 | verbatim | L10074-10261 | Entregado del M29.4. |
| `equipo.yaml` | M30.5 | verbatim | L10383-10439 | Entregado del M30.5. |
| `equipo.py` | M30.5 | verbatim | L10450-10539 | Entregado del M30.5. |
| `src/core/trabajos.py` | M21.5 | verbatim | L7419-7620 | Entregado del M21.5. |
| `src/core/politica.py` | M26.5 | verbatim | L9250-9375 | Entregado del M26.5. |
| `plataforma/estado.py` | M32.2 | verbatim | L10738-10771 | Un pool, un checkpointer y un store para toda la plataforma: el estado deja de ser de cada agente. |
| `plataforma/registro.py` | M32.3 | verbatim | L10826-10870 | El control plane resolviendo un id a paquete y fabrica. Sin publicacion no hay produccion. |
| `plataforma/catalogo.py` | M33.6 | verbatim | L11029-11099 | El resolutor del catalogo compartido: seleccion dinamica por contexto y permisos, con el sello que invalida la cache. |
| `plataforma/trazas.py` | M36.6 | verbatim | L12814-12876 | El esquema de traza del 36.1 como codigo: la unidad de observacion de una flota es la decision, no la CPU. |
| `gateway/config.yaml` | M0.5 | verbatim | L316-403 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L414-420 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L264-290 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L482-507 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L811-847 | El core bancario del 3.3 --- su import de datetime, los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L795-882, L893-953, L961-1034 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1103-1150 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1243-1344 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.3 | verbatim | L1522-1744 | Entregado del M5.3. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1901-1915 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1854-1893 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1935-2035 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L2620-2653, L2661-2673, L2718-2767, L2781-2807 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L5836-5889 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `db/schema.sql` | M21.5 | patch | L7628-7669 | banco.trabajos y banco.efectos (cola con leases y libro mayor de la saga). El libro dice literalmente que van al final del db/schema.sql del 7.6. |
| `db/schema.sql` | M35.6 | patch | L12621-12680 | banco.aprobaciones (la cola de aprobaciones con su receipt firmado). El libro dice literalmente que va al final del db/schema.sql del 7.6, junto a banco.trabajos. |
| `db/schema.sql` | M34.7 | patch | L11392-11441 | banco.supresiones y los cuatro ALTER de la supresion RGPD (aprobaciones, manuales, registro_ia). Va detras de aprobaciones: sus ALTER la necesitan creada. |
| `src/rag/indexar.py` | M7.4 | verbatim | L2436-2457 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: texto y meta son las variables del bucle del lector. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2882-2918 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2929-2981 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2992-3129 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L3180-3243 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L3563-3614, L3625-3663, L3674-3740, L3748-3857 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/agents/supervisor/supervisor.py` | M23.5 | patch | L8278-8359 | Anadido del M23.5. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L3983-4050 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L4058-4102 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L4205-4307, L4315-4334 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L6268-6281 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L4451-4557 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6137-6186 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6244-6260 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L4589-4700 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L4780-4844 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L4855-4943 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L5045-5136 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L5702-5767 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L5906-5943 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L5947-5972 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L6096-6129 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/despliegue-chat.yaml` | M27.2 | patch | L9447-9466 | Anadido del M27.2. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L6200-6230 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L6408-6452 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L6573-6603 | El ContextContract y el contrato de triaje. Valida contra schemas/context-contract.schema.json. |
| `config/model_routing.yaml` | M19.6 | verbatim | L6859-6895 | El fichero completo del 19.6: las rutas del 19.2 fusionadas con topes, canary y degradar. Dos bloques con la misma clave raiz no son un YAML. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L6949-6998 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `tools/operar_contabilidad_z.capability.yaml` | M26.3 | verbatim | L9203-9224 | El manifiesto de computer use del 26.3: la capacidad operar-aplicacion con su risk_tier y su step budget. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L7015-7062 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L7080-7105 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L7748-7763 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L8040-8054 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/memoria.py` | M34.1 | verbatim | L11172-11187 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.7 | patch | L11449-11569 | Anadido del M34.7. |
| `src/core/memoria.py` | M34.7 | patch | L11573-11617, L11625-11709, L11717-11755, L11763-11811 |  |
| `src/evals/medidas.py` | M15.7 | verbatim | L5319-5448 | Entregado del M15.7. |
| `src/evals/medidas.py` | M15.7 | patch | L5475-5547 | Anadido del M15.7. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L8816-8829 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L10597-10638 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L10788-10814 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L12946-13105, L13116-13238 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
