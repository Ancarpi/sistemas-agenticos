# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**
se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 13781 lineas. 72 ficheros, 89 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `src/core/memoria.sql` | M34.7 | verbatim | L11107-11197 | Entregado del M34.7. |
| `tests/test_registro.py` | M16.7 | verbatim | L5950-5977 | Entregado del M16.7. |
| `tests/test_art50.py` | M16.7 | verbatim | L5930-5946 | Anadido del M16.7. |
| `src/core/supresion.py` | M34.7 | verbatim | L11624-11818 | Entregado del M34.7. |
| `src/rag/responder.py` | M7.5 | verbatim | L2443-2539 | Entregado del M7.5. |
| `evals/run_rag_eval.py` | M8.3 | verbatim | L3264-3391 | Entregado del M8.3. |
| `src/core/hitl.py` | M35.6 | verbatim | L12073-12344 | Entregado del M35.6. |
| `src/core/router.py` | M19.6 | verbatim | L6632-6772 | Entregado del M19.6. |
| `src/core/catalogo_tools.py` | M20.6 | verbatim | L7040-7182 | Entregado del M20.6. |
| `src/evals/trayectoria.py` | M25.7 | verbatim | L8717-8789 | Entregado del M25.7. |
| `src/evals/trayectoria.py` | M25.7 | patch | L8797-8872 | Anadido del M25.7. |
| `src/rag/trocear.py` | M7.3 | verbatim | L2144-2372 | Entregado del M7.3. |
| `src/channels/confianza.py` | M22.5 | verbatim | L7662-7752 | Entregado del M22.5. |
| `src/agents/handoff.py` | M23.5 | verbatim | L7995-8144 | Entregado del M23.5. |
| `src/rag/gobierno.sql` | M24.6 | verbatim | L8374-8436 | Entregado del M24.6. |
| `src/rag/gobierno.py` | M24.6 | verbatim | L8444-8566 | Entregado del M24.6. |
| `config/politica.yaml` | M26.2 | verbatim | L8987-9033 | Entregado del M26.2. |
| `src/ops/migrar_checkpoints.py` | M27.4 | verbatim | L9326-9457 | Entregado del M27.4. |
| `runbooks/deriva.py` | M28.5 | verbatim | L9703-9792 | Entregado del M28.5. |
| `src/finops/coste_por_resolucion.py` | M29.4 | verbatim | L9894-10081 | Entregado del M29.4. |
| `equipo.yaml` | M30.5 | verbatim | L10196-10251 | Entregado del M30.5. |
| `equipo.py` | M30.5 | verbatim | L10262-10351 | Entregado del M30.5. |
| `src/core/trabajos.py` | M21.5 | verbatim | L7307-7503 | Entregado del M21.5. |
| `src/core/politica.py` | M26.5 | verbatim | L9084-9209 | Entregado del M26.5. |
| `plataforma/estado.py` | M32.2 | verbatim | L10546-10579 | Un pool, un checkpointer y un store para toda la plataforma: el estado deja de ser de cada agente. |
| `plataforma/registro.py` | M32.3 | verbatim | L10634-10678 | El control plane resolviendo un id a paquete y fabrica. Sin publicacion no hay produccion. |
| `plataforma/catalogo.py` | M33.6 | verbatim | L10837-10902 | El resolutor del catalogo compartido: seleccion dinamica por contexto y permisos, con el sello que invalida la cache. |
| `plataforma/trazas.py` | M36.6 | verbatim | L12539-12601 | El esquema de traza del 36.1 como codigo: la unidad de observacion de una flota es la decision, no la CPU. |
| `gateway/config.yaml` | M0.5 | verbatim | L294-372 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L383-389 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L242-268 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L451-476 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L780-816 | El core bancario del 3.3 --- su import de datetime, los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L764-851, L862-922, L930-1003 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1072-1119 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1212-1312 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.3 | verbatim | L1490-1712 | Entregado del M5.3. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1869-1883 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1822-1861 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1903-2003 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L2588-2621, L2629-2641, L2686-2735, L2749-2775 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L5786-5839 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `db/schema.sql` | M21.5 | patch | L7511-7552 | banco.trabajos y banco.efectos (cola con leases y libro mayor de la saga). El libro dice literalmente que van al final del db/schema.sql del 7.6. |
| `db/schema.sql` | M35.6 | patch | L12355-12405 | banco.aprobaciones (la cola de aprobaciones con su receipt firmado). El libro dice literalmente que va al final del db/schema.sql del 7.6, junto a banco.trabajos. |
| `db/schema.sql` | M34.7 | patch | L11205-11269 | banco.supresiones y los cuatro ALTER de la supresion RGPD (aprobaciones, manuales, registro_ia). Va detras de aprobaciones: sus ALTER la necesitan creada. |
| `src/rag/indexar.py` | M7.4 | verbatim | L2404-2425 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: texto y meta son las variables del bucle del lector. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2850-2883 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2894-2945 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2956-3090 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L3151-3214 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L3534-3585, L3596-3634, L3645-3711, L3719-3828 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/agents/supervisor/supervisor.py` | M23.5 | patch | L8161-8242 | Anadido del M23.5. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L3954-4018 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L4026-4070 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L4173-4279, L4287-4302 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L6217-6230 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L4419-4525 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6086-6135 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6193-6209 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L4557-4663 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L4743-4807 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L4818-4902 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L5004-5095 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L5652-5717 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L5856-5893 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L5897-5922 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L6045-6078 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/despliegue-chat.yaml` | M27.2 | patch | L9281-9300 | Anadido del M27.2. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L6149-6179 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L6357-6401 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L6502-6532 | El ContextContract y el contrato de triaje. Valida contra schemas/context-contract.schema.json. |
| `config/model_routing.yaml` | M19.2 | verbatim | L6554-6575 | Politica de routing por tarea, con presupuesto de pensamiento y de coste. |
| `config/model_routing.yaml` | M19.6 | patch | L6780-6796 | Anadido del M19.6. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L6850-6899 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L6916-6962 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L6980-7005 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L7631-7646 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L7923-7937 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/memoria.py` | M34.1 | verbatim | L10975-10990 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.7 | patch | L11277-11398 | Anadido del M34.7. |
| `src/core/memoria.py` | M34.7 | patch | L11402-11616 |  |
| `src/evals/medidas.py` | M15.7 | verbatim | L5270-5398 | Entregado del M15.7. |
| `src/evals/medidas.py` | M15.7 | patch | L5425-5497 | Anadido del M15.7. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L8679-8692 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L10409-10450 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L10596-10622 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L12662-12815, L12826-12945 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
