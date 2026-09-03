# webhook_slack.py --- la piel. El cerebro sigue siendo el mismo.
import hashlib
import hmac
import json
import os

import httpx
from fastapi import (BackgroundTasks, FastAPI, Header, Request,
                     Response)

from canal_chat import canal_chat        # otra vez el 6.3, intacto
from servidor import AVISO               # el mismo texto del 12.5

api = FastAPI()
SECRETO = os.environ["SLACK_SIGNING_SECRET"].encode()
BOT = {"Authorization": "Bearer " + os.environ["SLACK_BOT_TOKEN"]}


async def slack(metodo: str, cuerpo: dict) -> dict:
    async with httpx.AsyncClient() as cli:
        r = await cli.post(f"https://slack.com/api/{metodo}",
                           json=cuerpo, headers=BOT)
    return r.json()


async def publicar(canal: str, hilo_ts: str, texto: str) -> str:
    r = await slack("chat.postMessage", {"channel": canal,
                                         "thread_ts": hilo_ts,
                                         "text": texto})
    return r["ts"]


async def editar(canal: str, hilo_ts: str, ts, texto: str) -> str:
    if ts is None:                      # todavía no hay que editar
        return await publicar(canal, hilo_ts, texto)
    await slack("chat.update", {"channel": canal, "ts": ts,
                                "text": texto})
    return ts


def referencia_de(texto: str) -> str:
    # EstadoBackoffice la exige (6.3). En web va en el JSON; aquí
    # se saca del mensaje, y si no viene el triaje la pedirá.
    for palabra in texto.split():
        if palabra.startswith("REF-"):
            return palabra
    return ""


async def entregar_en_slack(hilo: str, ev: dict):
    canal = ev["channel"]
    hilo_ts = ev.get("thread_ts", ev["ts"])
    if "thread_ts" not in ev:
        # Art. 50: hilo nuevo, primer mensaje. Aquí no hay pie de
        # página donde esconderlo, y por eso vive en el flujo.
        await publicar(canal, hilo_ts, AVISO)
    # Sin token a token: la actividad EDITA un único mensaje y la
    # respuesta se acumula y se manda entera.
    actividad, trozos = None, []
    async for salida in canal_chat(ev["text"],
                                   referencia_de(ev["text"]), hilo):
        if salida["tipo"] == "token":
            trozos.append(salida["texto"])
        elif salida["tipo"] == "actividad":
            actividad = await editar(canal, hilo_ts, actividad,
                                     salida["texto"])
    await publicar(canal, hilo_ts, "".join(trozos))


@api.post("/slack/eventos")
async def eventos(req: Request, tareas: BackgroundTasks,
                  x_slack_request_timestamp: str = Header(),
                  x_slack_signature: str = Header(),
                  x_slack_retry_num: str | None = Header(None)):
    # El cuerpo CRUDO: si parseas y vuelves a serializar, el HMAC no
    # cuadra nunca y buscarás el fallo en la clave, que está bien.
    crudo = await req.body()
    base = f"v0:{x_slack_request_timestamp}:".encode() + crudo
    mia = "v0=" + hmac.new(SECRETO, base, hashlib.sha256).hexdigest()
    # compare_digest con dos str exige ASCII en los dos: una firma
    # con un solo carácter raro lanzaría UnicodeEncodeError y daría
    # un 500 --- crash sin autenticar --- en vez del 401 que toca.
    firma = x_slack_signature.encode("ascii", "ignore")
    if not hmac.compare_digest(mia.encode(), firma):
        return Response(status_code=401)
    cuerpo = json.loads(crudo)
    # El handshake de alta viene firmado pero SIN clave 'event'.
    # Sin estas dos líneas, Slack nunca habilita el endpoint.
    if cuerpo.get("type") == "url_verification":
        return {"challenge": cuerpo["challenge"]}
    # Lo que evita que un turno de 12 s se genere --- y se cobre ---
    # cuatro veces es el 200 del final, que sale en 20 ms. Este
    # guard es la red por si ese ack se pierde de camino. A escala
    # se deduplica por event_id en tabla, no por cabecera: así un
    # evento genuinamente perdido sí se reentrega.
    if x_slack_retry_num:
        return Response(status_code=200)
    ev = cuerpo["event"]
    # El hilo del canal ES el thread_id: mismo checkpoint, otra piel.
    hilo = f"slack:{ev['channel']}:{ev.get('thread_ts', ev['ts'])}"
    tareas.add_task(entregar_en_slack, hilo, ev)
    return Response(status_code=200)    # el ack va ANTES del agente
