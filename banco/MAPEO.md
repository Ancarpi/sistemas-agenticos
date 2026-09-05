# MAPEO --- que modulo del libro entrega cada fichero

**Generado por `tools/extraer_banco/extraer_banco.py`. No se edita a mano:**
se edita `tools/extraer_banco/mapeo.yaml` y se vuelve a ejecutar el script.

Libro de origen: 13894 lineas. 72 ficheros, 89 entradas de mapeo.

| Fichero | Modulo | Modo | Lineas del libro | Nota |
|---|---|---|---|---|
| `src/core/memoria.sql` | M34.7 | verbatim | L11137-11228 | Entregado del M34.7. |
| `tests/test_registro.py` | M16.7 | verbatim | L5963-5991 | Entregado del M16.7. |
| `tests/test_art50.py` | M16.7 | verbatim | L5943-5959 | Anadido del M16.7. |
| `src/core/supresion.py` | M34.7 | verbatim | L11665-11886 | Entregado del M34.7. |
| `src/rag/responder.py` | M7.5 | verbatim | L2444-2540 | Entregado del M7.5. |
| `evals/run_rag_eval.py` | M8.3 | verbatim | L3271-3398 | Entregado del M8.3. |
| `src/core/hitl.py` | M35.6 | verbatim | L12141-12451 | Entregado del M35.6. |
| `src/core/router.py` | M19.6 | verbatim | L6646-6786 | Entregado del M19.6. |
| `src/core/catalogo_tools.py` | M20.6 | verbatim | L7054-7196 | Entregado del M20.6. |
| `src/evals/trayectoria.py` | M25.7 | verbatim | L8736-8808 | Entregado del M25.7. |
| `src/evals/trayectoria.py` | M25.7 | patch | L8816-8891 | Anadido del M25.7. |
| `src/rag/trocear.py` | M7.3 | verbatim | L2145-2373 | Entregado del M7.3. |
| `src/channels/confianza.py` | M22.5 | verbatim | L7681-7771 | Entregado del M22.5. |
| `src/agents/handoff.py` | M23.5 | verbatim | L8014-8163 | Entregado del M23.5. |
| `src/rag/gobierno.sql` | M24.6 | verbatim | L8393-8455 | Entregado del M24.6. |
| `src/rag/gobierno.py` | M24.6 | verbatim | L8463-8585 | Entregado del M24.6. |
| `config/politica.yaml` | M26.2 | verbatim | L9006-9052 | Entregado del M26.2. |
| `src/ops/migrar_checkpoints.py` | M27.4 | verbatim | L9345-9482 | Entregado del M27.4. |
| `runbooks/deriva.py` | M28.5 | verbatim | L9728-9817 | Entregado del M28.5. |
| `src/finops/coste_por_resolucion.py` | M29.4 | verbatim | L9919-10106 | Entregado del M29.4. |
| `equipo.yaml` | M30.5 | verbatim | L10221-10276 | Entregado del M30.5. |
| `equipo.py` | M30.5 | verbatim | L10287-10376 | Entregado del M30.5. |
| `src/core/trabajos.py` | M21.5 | verbatim | L7321-7522 | Entregado del M21.5. |
| `src/core/politica.py` | M26.5 | verbatim | L9103-9228 | Entregado del M26.5. |
| `plataforma/estado.py` | M32.2 | verbatim | L10571-10604 | Un pool, un checkpointer y un store para toda la plataforma: el estado deja de ser de cada agente. |
| `plataforma/registro.py` | M32.3 | verbatim | L10659-10703 | El control plane resolviendo un id a paquete y fabrica. Sin publicacion no hay produccion. |
| `plataforma/catalogo.py` | M33.6 | verbatim | L10862-10932 | El resolutor del catalogo compartido: seleccion dinamica por contexto y permisos, con el sello que invalida la cache. |
| `plataforma/trazas.py` | M36.6 | verbatim | L12646-12708 | El esquema de traza del 36.1 como codigo: la unidad de observacion de una flota es la decision, no la CPU. |
| `gateway/config.yaml` | M0.5 | verbatim | L294-372 | El gateway del 0.5: el unico fichero del sistema que nombra proveedores. Solo os.environ/, ni un secreto. |
| `gateway/.env.gateway.example` | M0.5 | verbatim | L383-389 | Plantilla del .env del gateway. Los valores del libro ya son marcadores. |
| `src/core/models.py` | M0.4 | verbatim | L242-268 | La fabrica get_model()/get_embeddings(). Ruta obligada por el Ejercicio 0.1: de ella tira el resto del libro. |
| `src/core/models_local.py` | M0.5 | verbatim | L451-476 | Variante sin gateway: los alias se resuelven en la fabrica y el resto del repo no se entera. |
| `src/core/banco.py` | M3.3 | verbatim | L780-816 | El core bancario del 3.3 --- su import de datetime, los dos dicts y eur(). El 3.3 dice que en el 9.2 salen aqui, y supervisor.py los importa de esta ruta. |
| `src/agents/nano_agent.py` | M3.3 | verbatim | L764-851, L862-922, L930-1003 | Las tres piezas del 3.3 en orden: banco y herramientas, el velo (el JSON Schema a mano) y el bucle. |
| `src/agents/backoffice/herramientas.py` | M4.1 | verbatim | L1072-1119 | Las cuatro del 3.3 con @tool: el docstring vuelve a ser el esquema. |
| `src/agents/backoffice/agente_backoffice.py` | M4.3 | verbatim | L1212-1313 | El nano_agent industrializado: middleware, interrupt_on y checkpointer. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M5.3 | verbatim | L1491-1713 | Entregado del M5.3. |
| `src/agents/conciliacion/grafo_conciliacion.py` | M6.3 | patch | L1870-1884 | El nodo investigar del 6.3, que el propio libro coloca en este fichero. |
| `src/channels/chat/canal_chat.py` | M6.3 | verbatim | L1823-1862 | El generador que emite actividad y tokens a la vez. Es el cerebro que importan servidor.py y webhook_slack.py. |
| `src/agents/conciliacion/fanout_nocturno.py` | M6.4 | verbatim | L1904-2004 | El fan-out con Send: triaje en paralelo de un lote de 20. |
| `db/schema.sql` | M7.6 | verbatim | L2589-2622, L2630-2642, L2687-2736, L2750-2776 | Corpus con metadatos tipados, indice HNSW, mod-97 con su CHECK y la RLS. Los tres bloques del 7.6 que empiezan por NO va en schema.sql se quedan en el libro. |
| `db/schema.sql` | M16.6 | patch | L5799-5852 | registro_ia (Art. 12). El libro dice literalmente que va en el schema.sql del 7.6. |
| `db/schema.sql` | M21.5 | patch | L7530-7571 | banco.trabajos y banco.efectos (cola con leases y libro mayor de la saga). El libro dice literalmente que van al final del db/schema.sql del 7.6. |
| `db/schema.sql` | M35.6 | patch | L12462-12512 | banco.aprobaciones (la cola de aprobaciones con su receipt firmado). El libro dice literalmente que va al final del db/schema.sql del 7.6, junto a banco.trabajos. |
| `db/schema.sql` | M34.7 | patch | L11236-11303 | banco.supresiones y los cuatro ALTER de la supresion RGPD (aprobaciones, manuales, registro_ia). Va detras de aprobaciones: sus ALTER la necesitan creada. |
| `src/rag/indexar.py` | M7.4 | verbatim | L2405-2426 | PGEngine con driver explicito postgresql+psycopg:// y create_sync. Fragmento: texto y meta son las variables del bucle del lector. |
| `src/rag/08_hibrida.sql` | M8.1 | verbatim | L2851-2887 | Migracion del lado lexico: tsvector, GIN y unaccent. |
| `src/rag/hibrida.sql` | M8.1 | verbatim | L2898-2949 | Las dos ramas en un solo viaje a la base. |
| `src/rag/hibrida.py` | M8.1 | verbatim | L2960-3097 | Busqueda hibrida sobre la tabla del 7.6, con el SET LOCAL de niveles dentro de la transaccion. |
| `src/rag/rerank.py` | M8.2 | verbatim | L3158-3221 | El cross-encoder rerank-multilingue servido por el gateway. |
| `src/agents/supervisor/supervisor.py` | M9.2 | verbatim | L3541-3592, L3603-3641, L3652-3718, L3726-3835 | Las cuatro piezas del 9.2: el estado que es el contrato, el supervisor, las herramientas y los dos trabajadores. |
| `src/agents/supervisor/supervisor.py` | M23.5 | patch | L8180-8261 | Anadido del M23.5. |
| `src/core/mcp_core.py` | M10.2 | verbatim | L3961-4025 | El core expuesto por MCP: FastMCP, transporte streamable-http y stateless_http=True. |
| `src/agents/cliente_core.py` | M10.2 | verbatim | L4033-4077 | El cliente con allow-list firmada por sha256 y tool_name_prefix=True. |
| `src/agents/allowlist_mcp.json` | M10.2 | plantilla | --- | Allow-list de descripciones aprobadas. cliente_core.py la lee en docs/mcp-aprobadas.json: costura pendiente, ver COSTURAS.md. |
| `src/channels/backend/batch_nocturno.py` | M11.5 | verbatim | L4180-4282, L4290-4309 | El quinto canal: worker con candado, presupuesto consultado al gateway, cola de aprobacion e informe de las 8:00. |
| `src/channels/backend/batch_nocturno.py` | M17.2 | patch | L6231-6244 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M12.5 | verbatim | L4426-4532 | El transporte y nada mas: SSE, el aviso del Art. 50 y el cerebro del 6.3 importado sin tocar. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6100-6149 | Sondas de liveness y readiness con cache de 5 s. Esta si se pega al final, como dice el libro. |
| `src/channels/chat/servidor.py` | M17.2 | patch | L6207-6223 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/channels/slack/webhook_slack.py` | M12.6 | verbatim | L4564-4675 | La segunda piel: firma HMAC, el plazo de 3 s de Slack y el mismo cerebro del 6.3. |
| `src/agents/voz/grafo_voz.py` | M13.4 | verbatim | L4755-4819 | El cerebro de la llamada: dos herramientas y wrap_tool_call. |
| `src/channels/voz/agente_voz.py` | M13.4 | verbatim | L4830-4914 | La piel de tiempo real (LiveKit). El cerebro se importa de grafo_voz. |
| `src/channels/avatar/cara.py` | M14.2 | verbatim | L5016-5107 | El avatar como interruptor sobre la sesion del 13.4. |
| `src/core/cumplimiento.py` | M16.5 | verbatim | L5665-5730 | Los dos articulos que se implementan igual en las cinco superficies: el aviso del 50 y el registro del 12. |
| `compliance/clasificacion-ia.yaml` | M16.7 | verbatim | L5869-5906 | El Anexo III en el repo: la clasificacion de riesgo como codigo, por caso de uso. |
| `tests/test_clasificacion.py` | M16.7 | verbatim | L5910-5935 | Lo que separa un control de una intencion: el test de la clasificacion. |
| `deploy/despliegue-chat.yaml` | M17.2 | verbatim | L6059-6092 | El servidor.py del 12.5 en un cluster: sondas, preStop y gracia de 120 s. |
| `deploy/despliegue-chat.yaml` | M27.2 | patch | L9300-9319 | Anadido del M27.2. |
| `deploy/autoescalado.yaml` | M17.2 | verbatim | L6163-6193 | KEDA por profundidad de cola, nunca por CPU. |
| `src/core/identidad.py` | M18.3 | verbatim | L6371-6415 | Quien es el hilo: dos funciones separan cinco canales de cinco sistemas. |
| `src/core/context_contracts.py` | M19.1 | verbatim | L6516-6546 | El ContextContract y el contrato de triaje. Valida contra schemas/context-contract.schema.json. |
| `config/model_routing.yaml` | M19.2 | verbatim | L6568-6589 | Politica de routing por tarea, con presupuesto de pensamiento y de coste. |
| `config/model_routing.yaml` | M19.6 | patch | L6794-6810 | Anadido del M19.6. |
| `tools/bloquear_tarjeta.capability.yaml` | M20.1 | verbatim | L6864-6913 | Tool Capability Manifest. Valida contra schemas/tool-capability.schema.json. |
| `src/agents/cards_disputes/herramientas.py` | M20.2 | verbatim | L6930-6976 | read-plan-dry-run-commit con clave de idempotencia y outbox. Es el entrypoint que declara catalogo/cards-disputes/agent.yaml. |
| `src/core/contratos.py` | M20.3 | verbatim | L6994-7019 | ToolError tipado: el error como lenguaje de coordinacion, devuelto como ToolMessage y nunca como excepcion cruda. |
| `src/core/contratos.py` | M22.3 | patch | L7650-7665 | HumanHandoffPacket: el escalado a humano como producto. Trae sus imports repetidos, tal cual estan en el libro. |
| `src/core/contratos.py` | M23.1 | patch | L7942-7956 | HandoffContract y su campo authority: la frontera entre agentes. |
| `src/core/memoria.py` | M34.1 | verbatim | L11005-11020 | MemoryRecord: sin owner, sensibilidad, TTL y procedencia no hay memoria gobernada. |
| `src/core/memoria.py` | M34.7 | patch | L11311-11434 | Anadido del M34.7. |
| `src/core/memoria.py` | M34.7 | patch | L11438-11657 |  |
| `src/evals/medidas.py` | M15.7 | verbatim | L5282-5411 | Entregado del M15.7. |
| `src/evals/medidas.py` | M15.7 | patch | L5438-5510 | Anadido del M15.7. |
| `.github/workflows/agent-evals.yml` | M25.5 | verbatim | L8698-8711 | Extracto conceptual, igual que en el libro: no es un workflow completo. |
| `aceptacion.py` | M31.2 | verbatim | L10434-10475 | La puerta del capstone: seis medidas, semilla, pases e intervalo, con el veredicto NO CONCLUYENTE. |
| `catalogo/cards-disputes/agent.yaml` | M32.3 | verbatim | L10621-10647 | Agent Package publicable. Valida contra schemas/agent-package.schema.json. |
| `plataforma/runtime.py` | M37.2 | verbatim | L12769-12922, L12933-13053 | Nadie importa un grafo: se pide por id, con el sello del catalogo en la clave de la cache. La politica y el HITL van en el mismo wrap_tool_call. |
| `smoke_test.py` | Ej. 0.1 | plantilla | --- | Andamio del Ejercicio 0.1: dos alias, latencia y tokens, Postgres y traza. El unico fichero del repo que corre solo. |

`verbatim` = el bloque del libro tal cual. `patch` = anadido al final del
fichero, con un marcador que nombra su modulo; las que ademas exigen una
decision estan en `COSTURAS.md`. `plantilla` = andamio escrito para el
paquete, no codigo del libro.
