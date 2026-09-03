# cara.py --- el avatar, un interruptor sobre la sesión del 13.4.
import asyncio
import logging
import os

from livekit import rtc
from livekit.agents import AgentSession, utils
from livekit.plugins import tavus

TAVUS = "https://tavusapi.com/v2"
reg = logging.getLogger("cara")


def _viva(t) -> bool:
    return t is not None and not t.done()


class Cara:
    def __init__(self, ses: AgentSession, sala: rtc.Room,
                 ocio: float = 90.0):
        self.ses, self.sala, self.ocio = ses, sala, ocio
        self.cara_id = os.environ["TAVUS_FACE_ID"]
        self.avatar, self.reloj = None, None
        self.arranque, self.cierre = None, None
        # El camino de vuelta: el último eslabón de la cadena de
        # audio es el track que RoomIO publicó en la sala; se
        # captura AHORA, porque la cara lo va a tapar.
        self.voz = ses.output.audio
        while self.voz.next_in_chain is not None:
            self.voz = self.voz.next_in_chain
        sala.on("participant_disconnected", self._caida)

    async def encender(self) -> bool:
        if self.avatar:
            return True
        self.avatar = tavus.AvatarSession(face_id=self.cara_id)
        try:
            await self.avatar.start(self.ses, self.sala)
            await self.avatar.wait_for_join(timeout=8.0)
        except Exception:
            reg.exception("la cara no entró; seguimos en voz")
            await self.apagar("arranque")
            return False
        self.tocar()
        return True

    async def apagar(self, motivo: str) -> None:
        # LA línea del módulo: el sumidero de audio de la sesión
        # ES el avatar, y apagar la cara sin devolver la cola al
        # track de la sala deja la conversación muda.
        self.ses.output.replace_audio_tail(self.voz)
        avatar, self.avatar = self.avatar, None
        if avatar is None:
            return
        await avatar.aclose()            # lo saca de la sala...
        if avatar.conversation_id:       # ...y esto deja de pagar
            await self._cerrar_remota(avatar.conversation_id)
        reg.warning("cara apagada (%s); la voz sigue", motivo)

    async def _cerrar_remota(self, conv: str) -> None:
        # Dinero, no disponibilidad: si el cierre remoto falla,
        # se anota y la conversación continúa en voz.
        try:
            http = utils.http_context.http_session()
            async with http.post(
                f"{TAVUS}/conversations/{conv}/end",
                headers={"x-api-key": os.environ["TAVUS_API_KEY"]},
            ) as r:
                if r.status >= 400:
                    reg.warning("Tavus no cerró %s: HTTP %s",
                                conv, r.status)
        except Exception:
            reg.exception("cierre remoto fallido: mira el panel")

    def tocar(self) -> None:             # cada turno del usuario
        # Doble oficio: rearma el reloj y, si la cara se había
        # apagado por inactividad, la vuelve a llamar.
        if not self.avatar and not _viva(self.arranque):
            self.arranque = asyncio.create_task(self.encender())
        if self.reloj:
            self.reloj.cancel()
        self.reloj = asyncio.create_task(self._ocioso())

    async def _ocioso(self) -> None:
        await asyncio.sleep(self.ocio)
        await self.apagar("inactividad")

    def _caida(self, quien: rtc.RemoteParticipant) -> None:
        # La referencia se guarda: una tarea suelta se la puede
        # llevar el recolector a mitad de la degradación.
        if self.avatar and quien.identity == self.avatar.avatar_identity:
            self.cierre = asyncio.create_task(self.apagar("proveedor"))
