# runtime.py --- nadie importa un grafo: se pide por id. Solo
# `autorizar` (Ejercicio 35.1) y `encolar` (35.2) son tuyos.
import hashlib
import json
import os
import uuid
from importlib import import_module

import yaml
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call    # el 4.2
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.types import interrupt                     # el 6.1
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import identidad                            # el fichero del 18.3
from herramientas import (buscar_transferencia, escalar_a_humano,
                          historial_cuenta, marcar_resuelta)  # 4.1
from hitl import encolar                    # Ejercicio 35.2
from politica import autorizar              # 26.2 + Ejercicio 35.1
from src.core.models import get_embeddings, get_model    # el 0.4
from trazas import atributos                # el fichero del 36.6

DB, ENTORNO = os.environ["DATABASE_URL"], os.environ["ENTORNO"]
SAVER = STORE = None        # los abre `arrancar()`, no el `import`

# El catálogo del Ejercicio 33.1 en su forma más pequeña que
# funciona: nombre -> (tool, `version` y `status` del 33.4, clase
# de dato y peldaño del Anexo H). Las dos últimas columnas no
# adornan: sin ellas la política del 35.1 decide a ciegas. Las
# cuatro del 4.1; las de MCP llegan por el `get_tools()` del 10.2.
CATALOGO = {
    "core.sepa.buscar": (buscar_transferencia, "1.0.0", "active",
                         "confidential", "L0"),
    "core.sepa.historial": (historial_cuenta, "1.1.0", "active",
                            "confidential", "L0"),
    "core.sepa.resolver": (marcar_resuelta, "1.0.0", "active",
                           "internal", "L3"),
    "core.sepa.escalar": (escalar_a_humano, "1.0.0", "active",
                          "internal", "L3"),
}
CACHE = {}


async def arrancar():
    """Va en el `lifespan` del 17.2, antes del `yield`: las dos
    conexiones viven tanto como el proceso y el `with` del 5.2 y
    del 6.2 muere al cerrar su bloque. Y en variante ASÍNCRONA,
    porque `ejecutar` llama a `ainvoke`: sobre el saver síncrono el
    primer superpaso muere en `aget_tuple`, igual que la sonda del
    17.2. El `setup()` que el 5.2 y el 6.2 piden «la primera vez»
    es este; sin él, la primera base limpia no tiene `checkpoints`."""
    global SAVER, STORE
    pool = AsyncConnectionPool(DB, open=False, kwargs={
        "autocommit": True, "row_factory": dict_row})
    await pool.open()
    SAVER = AsyncPostgresSaver(pool)
    STORE = AsyncPostgresStore(         # el índice, como en el 6.2
        pool, index={"embed": get_embeddings(), "dims": 1024})
    await SAVER.setup()
    await STORE.setup()


def sello_catalogo() -> str:
    ternas = sorted((n, x[1], x[2]) for n, x in CATALOGO.items())
    return hashlib.sha256(repr(ternas).encode()).hexdigest()[:12]


def resolver(permitidas):
    """Su `tools_allowed` cortado por lo que el catálogo sirve HOY:
    una `retired` no llega, y eso es lo que debe pasar. Un nombre
    que no está en el catálogo es otra cosa --- un error de
    publicación ---, y por eso revienta aquí: servirlo callando da
    un agente con menos herramientas y ni un aviso. Falta el
    gateway del 33.3 en medio, y el agente no notará la diferencia
    el día que lo pongas."""
    return [CATALOGO[n][0] for n in permitidas
            if CATALOGO[n][2] == "active"]


def cargar(agente_id):
    """El `agent.yaml` del 32.3 tal cual se publicó, más la fábrica
    de su `entrypoint` si el paquete trae grafo propio. El que no
    lo trae lo monta el runtime, y así el `guardia` no es opcional
    para nadie."""
    with open(f"agents/{agente_id}/agent.yaml") as f:
        pk = yaml.safe_load(f)
    # La lista blanca de grafos del 18.3 --- allí, dos literales ---
    # la puebla el registro: son los que haya publicados.
    identidad.GRAFOS.add(pk["id"])
    ruta = pk.get("entrypoint")
    if not ruta:
        return pk, None
    modulo, _, objeto = ruta.partition(":")
    # El 32.3 lo escribe con barras, como uvicorn, y con barras no
    # hay módulo que importar: `src/agents/cards_disputes` no es
    # `src.agents.cards_disputes` para nadie más que para ti.
    modulo = modulo.replace("/", ".").removesuffix(".py")
    return pk, getattr(import_module(modulo), objeto)


def compilar(pk, sello, propio=None):
    """La clave lleva el sello del catálogo --- hash de las ternas
    (nombre, `version`, `status`) del 33.4 y de las filas de
    aprobación del 33.6: sin él, ni marcar una tool `retired` ni
    retirarle la aprobación revocan nada. `propio`: el grafo del
    paquete (9.2). El `guardia` es el de abajo, en este fichero."""
    clave = (pk["id"], pk["version"], sello)
    if clave in CACHE:
        return CACHE[clave]
    for vieja in [k for k in CACHE if k[2] != sello]:
        del CACHE[vieja]     # o cada revocación deja un grafo vivo
    tools = resolver(pk["tools_allowed"])
    if propio is not None:
        # El paquete con grafo propio NO se busca sus herramientas
        # ni su middleware: los recibe, o la revocación y la
        # política no le llegan. Migrar el supervisor del 9.2 es
        # eso --- `g` pasa a `g(tools, mw)` --- y llega sin
        # compilar: la durabilidad la pone la plataforma.
        CACHE[clave] = propio(tools, [guardia]).compile(
            checkpointer=SAVER, store=STORE)
    else:
        CACHE[clave] = create_agent(
            model=get_model(pk["models"]["supervisor"]), tools=tools,
            middleware=[guardia], checkpointer=SAVER, store=STORE)
    return CACHE[clave]


async def ejecutar(agente_id, sujeto, texto, proposito, humano):
    """El hilo no se inventa aquí: es el `hilo(grafo, sujeto)` del
    18.3 --- con el agente delante, porque el checkpointer indexa
    por thread_id ---, y `sujeto` llega con su clase: `cliente:C-99`.
    `humano` es quien delega y cómo se autenticó --- `{"id":
    "E-123", "auth": "strong"}` ---, los dos de la sesión del canal
    y ninguno del agente (35.3)."""
    pk, propio = cargar(agente_id)                      # el 32.3
    ctx = {"sujeto": sujeto, "humano": humano, "run": uuid.uuid4().hex,
           "proposito": proposito, "entorno": ENTORNO,
           "agente": {"id": pk["id"], "version": pk["version"]},
           "hilo": identidad.hilo(pk["id"], sujeto),       # 18.3
           "ns": (pk["tenant"], proposito, sujeto)}  # jamás el agente
    cfg = {"configurable": {"thread_id": ctx["hilo"]},
           "metadata": atributos(pk, ctx)}                 # 36.1
    return await compilar(pk, sello_catalogo(), propio).ainvoke(
        {"messages": [("user", texto)]}, cfg, context=ctx)
# La política y el HITL, en el mismo `wrap_tool_call` del 4.2 que
# ya usaste en el 13.4: una decisión por llamada, para los cuatro.
# Va debajo de `ejecutar`, en el mismo fichero, y `async` con
# `await` como aquel: uno síncrono invocado desde `ainvoke` no se
# ejecuta nunca --- aborta la primera llamada y se lleva por
# delante las dos fronteras que este apartado llama insaltables.
@wrap_tool_call
async def guardia(peticion, siguiente):
    ctx, llamada = peticion.runtime.context, peticion.tool_call
    clase, peldano = CATALOGO[llamada["name"]][3:]
    # El dict del 35.2 con sus seis claves, que son los seis
    # atributos que el Ejercicio 35.1 obliga a evaluar. `autorizar`
    # es ese policy engine y devuelve una de sus cinco cadenas. La
    # tool va por su nombre: `peticion.tool` es None si retirada.
    decision = autorizar({
        "subject": {"user_id": ctx["humano"]["id"],
                    "auth_level": ctx["humano"]["auth"]},
        "agent": ctx["agente"], "tool": {"id": llamada["name"]},
        "resource": {"account_owner": ctx["sujeto"],
                     "data_class": clase},
        "context": {"purpose": ctx["proposito"],
                    "env": ctx["entorno"]},
        "risk": {"autonomy_level": peldano}})
    # El `policy.decision` del 36.1, y en TODA llamada, no solo al
    # denegar: es el artefacto del tercer camino del 37.4, y una
    # denegación que no deja rastro no es un control, es una
    # opinión del proceso que la tomó.
    print(json.dumps({"policy.decision": decision,
                      "tool.id": llamada["name"],
                      "run.id": ctx["run"]}))
    if decision == "require_human":
        # El `interrupt()` va PRIMERO y no hay efecto externo por
        # encima (la regla del 11.5): al reanudar, este wrapper se
        # reejecuta desde su primera línea, y encolando arriba la
        # segunda vuelta deja una propuesta gemela, con su segundo
        # receipt, para un solo commit. La propuesta va en la
        # carga, que es lo que la pantalla de aprobación lee del
        # checkpoint; lo de abajo corre una sola vez, ya decidido.
        d = interrupt({"run": ctx["run"], "agente": ctx["agente"],
                       "accion": llamada["name"],
                       "propuesta": llamada["args"]})
        # Se reanuda con el hilo, nunca con el run. Y quien PROPONE
        # es el humano que delegó, jamás el agente (regla del 35.4).
        encolar(hilo=ctx["hilo"], run=ctx["run"],
                agente=ctx["agente"], propone=ctx["humano"]["id"],
                propuesta=llamada["args"], receipt=d)
        # `approve/reject` y `edit before commit` son dos filas del
        # 35.4: sin este reparto las tres cadenas caen en
        # `siguiente` y rechazar ejecuta igual que aprobar.
        if d["decision"] == "reject":
            return ToolMessage(f"RECHAZADO: {d['motivo_rechazo']}",
                               tool_call_id=llamada["id"])
        if d["decision"] == "edit":
            llamada["args"] = d["args"]     # el commit va editado
    elif decision != "allow":      # dry-run y step-up: aún no están
        return ToolMessage(f"política: {decision}",
                           tool_call_id=llamada["id"])
    return await siguiente(peticion)
