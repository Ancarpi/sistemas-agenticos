# agente_voz.py --- la piel de tiempo real. El cerebro aparece en
# una sola línea, la del adaptador.
from livekit import agents
from livekit.agents import (
    Agent, AgentSession, EndpointingOptions, InterruptionOptions,
    RoomInputOptions, TurnHandlingOptions,
)
from livekit.plugins import (
    cartesia, deepgram, langchain, noise_cancellation, silero,
)
from livekit.plugins.turn_detector.multilingual import (
    MultilingualModel,
)

from grafo_voz import construir_cerebro

SALUDO = ("Le atiende el asistente virtual de Banco Meridiano. "
          "Soy una inteligencia artificial y la llamada se graba. "
          "¿En qué puedo ayudarle?")


def prewarm(proc: agents.JobProcess):
    """Los dos ONNX, UNA vez por proceso. Cargarlos dentro de
    `entrypoint` es medio segundo en el camino de cada llamada, en
    el capítulo cuya tesis es que ese medio segundo se nota."""
    proc.userdata["vad"] = silero.VAD.load()
    proc.userdata["turnos"] = MultilingualModel()


async def cerebro(proc: agents.JobProcess):
    """`prewarm` es síncrono y abrir el MCP no lo es, así que el
    grafo se paga en la primera llamada del proceso y las demás
    lo reutilizan. Sin esto, cada llamada empieza pidiéndole el
    catálogo al core."""
    if "cerebro" not in proc.userdata:
        proc.userdata["cerebro"] = await construir_cerebro()
    return proc.userdata["cerebro"]


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],             # ¿hay voz?
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=langchain.LLMAdapter(
            graph=await cerebro(ctx.proc),
            stream_mode=["messages", "custom"],   # ver 13.5
        ),
        # Los nombres de modelo caducan: ver el aviso del 13.2.
        tts=cartesia.TTS(model="sonic-3", language="es"),
        turn_handling=TurnHandlingOptions(
            # ¿ha TERMINADO de hablar? Modelo semántico, no
            # silencio: es lo que pedía el 13.1, y trae español.
            turn_detection=ctx.proc.userdata["turnos"],
            endpointing=EndpointingOptions(min_delay=0.5,
                                           max_delay=3.0),
            # mode="vad" para que `min_words` mande: sin fijarlo,
            # decide el detector adaptativo. Y con él, que un
            # «ajá» no corte al agente.
            interruption=InterruptionOptions(mode="vad",
                                             min_duration=0.5,
                                             min_words=2),
        ),
    )
    # El prompt vive en UN sitio, el `system_prompt` del grafo:
    # `instructions` metería un segundo mensaje de sistema en el
    # contexto que viaja al adaptador. El M14 engancha el avatar
    # a esta misma sesión, sin tocar nada de esto.
    await session.start(
        agent=Agent(instructions=""), room=ctx.room,
        # En el AGENTE, no en el trunk: ver más abajo. Este
        # plugin es propietario y pide LiveKit Cloud.
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVCTelephony()),
    )
    await ctx.connect()
    await session.say(SALUDO, allow_interruptions=False)


if __name__ == "__main__":
    # `run_app` es el camino heredado --- el paquete ya lo marca
    # así ---; el moderno es `lk agent` sobre `AgentServer`.
    # agent_name es lo que busca la regla de reparto de abajo.
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint, prewarm_fnc=prewarm,
        agent_name="meridiano-voz"))
