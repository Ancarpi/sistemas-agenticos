# COSTURAS --- lo que el libro deja para aplicar a mano

**Generado por `tools/extraer_meridiano/extraer_meridiano.py`.**

Un bloque del libro que parchea otro fichero se extrae **al final** del
fichero destino, con un marcador que nombra su modulo. Cuando el orden
no importa, ese anadido ya es el estado final. Cuando si importa, el
script **no** intenta fusionarlo: pegarlo en su sitio es una decision, no
una operacion de texto. Estas son las que quedan pendientes.

| Destino | Modulo | Que hay que hacer |
|---|---|---|
| `src/channels/backend/batch_nocturno.py` | M17.2 | PENDIENTE. Apagado ordenado por SIGTERM: el libro lo pega justo encima de main(), y la condicion del bucle de tandas pasa a mirar PARANDO. |
| `src/channels/chat/servidor.py` | M17.2 | PENDIENTE. Lifespan y apagado ordenado: SUSTITUYE al FastAPI() del 12.5. Pegado al final reasigna api y el canal se queda sin rutas. |
| `src/core/politica.py` | M35.2 | PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta. |
| `src/core/memoria.py` | M34.5 | PENDIENTE. Las tres APIs tipadas de memoria con sus receipts: los cuerpos son ... y los tres tipos de receipt no existen todavia, asi que el modulo no importa hasta que los escribas. |

El resto de los `patch` de `MAPEO.md` son anadidos al final que no
piden nada mas: el fichero ya queda como tiene que quedar.

## Costura del M16.5

Las cinco costuras del aviso del Art. 50, una por superficie: cinco llevan aviso y la ultima prueba el Art. 14.

``` python
# Las costuras: una por superficie, y lo que hay que leer en
# ellas es en qué se diferencian. Cinco llevan aviso del 50; la
# última no es un aviso, es la fila que prueba el Art. 14.
# `anotar_aviso` es E/S bloqueante, así que en todo lo que corre
# dentro de un bucle de eventos va por `to_thread`: un INSERT
# síncrono en el saludo congela la llamada entera.

# 12.5 servidor.py --- sustituye a la constante AVISO. Es por
# HILO y no por turno: quien decide si toca es el checkpoint.
if nuevo:
    yield sse({"tipo": "aviso", "texto": AVISOS["chat"]})
    await asyncio.to_thread(anotar_aviso, "chat", cliente_id)

# 12.6 webhook.py --- el quinto canal, que se cuela por un
# import: `from servidor import AVISO` pasa a ser `from
# cumplimiento import AVISOS, anotar_aviso`. Mismo texto que el
# chat web, otra superficie, y por eso anota `slack`.
if "thread_ts" not in ev:
    await publicar(canal, hilo_ts, AVISOS["slack"])
    await asyncio.to_thread(anotar_aviso, "slack", hilo_ts)

# 13.4 agente_voz.py --- sustituye a SALUDO. `say` NO es una
# corrutina: devuelve un SpeechHandle. Lo bloqueante es esperar
# el handle, y el handle sabe si le cortaron.
h = session.say(AVISOS["voz"], allow_interruptions=False)
await h
await asyncio.to_thread(anotar_aviso, "voz", ctx.room.name,
                        interrumpido=h.interrupted)

# 14.2 cara.py --- el texto depende de si la cara llegó a entrar:
# sin cara no hay 50(2) que declarar, y declarar una cara que la
# degradación acaba de apagar es la forma de que el aviso mienta.
canal = "avatar" if await cara.encender() else "voz"
h = session.say(AVISOS[canal], allow_interruptions=False)
await h
await asyncio.to_thread(anotar_aviso, canal, ctx.room.name,
                        interrumpido=h.interrupted)

# 11.5 batch_nocturno.py --- aquí NO hay aviso del 50: no hay
# nadie con quien interactuar. Lo que hay es el 26(11), y va con
# el `cur` del lote: si la tanda se deshace, el registro también.
anotar("art26_decision", "backend", ref, cur=cur,
       veredicto=v["categoria"])

# 4.3 --- el Art. 14 no lo prueba el middleware, lo prueba la
# fila, y va donde se REANUDA el interrupt, no donde se lanza.
r = agente.invoke(Command(resume={"decisions": [d]}), HILO)
anotar("art14_aprobacion", "backend", ref,
       aprobador=quien, decision=d["type"])
```

## Costura del M14.2

La costura del avatar con el entrypoint del 13.4: nada de room_output_options, y el avatar despues de session.start.

``` python
from cara import Cara

cara = Cara(session, ctx.room)
session.on("user_input_transcribed", lambda _: cara.tocar())
await cara.encender()          # si devuelve False, hay voz
await session.say(SALUDO, allow_interruptions=False)
```
