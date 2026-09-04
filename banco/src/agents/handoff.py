# src/agents/handoff.py --- la frontera entre DOS agentes. El
# ContextContract del 19.1 contrata una llamada al modelo; esto
# contrata un traspaso, y se monta sobre el EstadoBanco del 9.2.
import hashlib
import re
from operator import add
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from src.core.context_contracts import ContextContract  # el 19.1
from src.agents.supervisor.supervisor import EstadoBanco, Hecho  # el 9.2

Autoridad = Literal["recomendar", "preparar", "ejecutar", "aprobar"]
ESCALA = ("recomendar", "preparar", "ejecutar", "aprobar")


class Presupuesto(BaseModel):
    """Lo que le queda AL HILO, no a la llamada. El 19.1 pone el
    tope de una llamada; lo que revienta en producción es la suma
    de treinta, y nadie estaba mirando esa suma."""
    tokens: int
    eur: float
    saltos: int

    @property
    def agotado(self) -> str | None:
        if self.saltos <= 0:
            return "saltos"
        if self.tokens <= 0:
            return "tokens"
        return "eur" if self.eur <= 0 else None


def restar(actual: Presupuesto, gasto: Presupuesto) -> Presupuesto:
    """Reducer de LangGraph: el presupuesto se descuenta EN EL
    ESTADO, nunca en la copia que viaja. Con dos ramas a la vez
    (23.2) cada copia se creería dueña del hilo entero."""
    return Presupuesto(tokens=actual.tokens - gasto.tokens,
                       eur=round(actual.eur - gasto.eur, 4),
                       saltos=actual.saltos - gasto.saltos)


class Procedencia(BaseModel):
    """Quién lo pidió y por qué. Llega intacta al cuarto agente,
    que así sabe si contesta a una persona esperando al teléfono o
    a una fila del batch del 11.5."""
    origen: Literal["cliente", "batch", "auditoria", "humano"]
    pedido_por: str
    motivo: str
    caso: str


class Traspaso(BaseModel):
    """Lo que cruza la frontera. Todo lo que no esté aquí se
    queda en el emisor, empezando por su transcripción."""
    de: str
    a: str
    encargo: str
    autoridad: Autoridad
    hechos: list[str]          # conclusiones citadas, no diálogo
    abiertas: list[str]        # lo que el emisor NO pudo cerrar
    herramientas: list[str]
    presupuesto: Presupuesto   # foto, no la fuente de la verdad
    procedencia: Procedencia
    recorrido: list[str] = Field(default_factory=list)


class EstadoTraspasado(EstadoBanco):
    """El estado del 9.2 con la frontera encima. `saltos` sigue
    siendo el techo bruto; `recorrido` es el techo con memoria."""
    autoridad: Autoridad                     # el techo del hilo
    procedencia: dict                        # fija durante el hilo
    presupuesto: Annotated[Presupuesto, restar]
    recorrido: Annotated[list[str], add]     # "destino:huella"
    traspaso: dict | None


class TraspasoMuerto(Exception):
    """El contrato negándose. Quien lo captura enruta a
    `responder` y lo dice; un traspaso muerto no se reintenta."""


def huella(encargo: str) -> str:
    """Un encargo reformulado es otro encargo. El mismo con otras
    mayúsculas y otros espacios, no."""
    return hashlib.sha1(
        " ".join(encargo.lower().split()).encode()).hexdigest()[:8]


def depurar(hechos: list[Hecho], c: ContextContract) -> list[str]:
    """Los `forbidden_patterns` del 19.1, aplicados al traspaso.
    El hecho que trae un IBAN dentro se queda en quien lo escribió
    y el destino recibe la retención, nunca el silencio."""
    salida = []
    for h in hechos:
        linea = f"{h['autor']}: {h['dato']}"
        if any(re.search(p, linea) for p in c.forbidden_patterns):
            linea = f"{h['autor']}: [retenido: dato sensible]"
        salida.append(linea)
    return salida


def emitir(estado: EstadoTraspasado, de: str, a: str, encargo: str,
           autoridad: Autoridad, concede: list[str],
           contrato: ContextContract) -> Traspaso:
    """Las cinco negativas del contrato. Ninguna pasa por modelo."""
    marca = f"{a}:{huella(encargo)}"
    if a == de:
        raise TraspasoMuerto(f"{de} se traspasa a sí mismo")
    if marca in estado["recorrido"]:
        # El bucle educado del 3.4, un nivel más arriba: el caso
        # vuelve a quien ya lo devolvió, con el encargo que falló.
        raise TraspasoMuerto(f"{a} ya recibió este encargo")
    if falta := estado["presupuesto"].agotado:
        raise TraspasoMuerto(f"presupuesto del hilo: {falta}")
    if ESCALA.index(autoridad) > ESCALA.index(estado["autoridad"]):
        # Nadie delega lo que no tiene. Sin esta línea, tres
        # traspasos ascienden un «recomendar» a un «ejecutar».
        raise TraspasoMuerto(f"{de} no puede conceder {autoridad}")
    # El emisor RESTRINGE. Ampliar lo visible es cosa del contrato
    # del destino, y ese lo escribió su dueño, no quien traspasa.
    herramientas = [h for h in concede if h in contrato.visible_tools]
    if autoridad in ("ejecutar", "aprobar") and not herramientas:
        raise TraspasoMuerto(f"{a} ejecutaría sin herramientas")
    return Traspaso(
        de=de, a=a, encargo=encargo, autoridad=autoridad,
        hechos=depurar(estado["hechos"], contrato),
        abiertas=[estado["devuelto_por"]] if estado["devuelto_por"]
        else [],
        herramientas=herramientas,
        presupuesto=estado["presupuesto"],
        procedencia=Procedencia(**estado["procedencia"]),
        recorrido=estado["recorrido"] + [marca])


def briefing(t: Traspaso) -> str:
    """La superficie de contacto entera del receptor, como en el
    9.2. Autoridad y presupuesto van DENTRO del prompt: el modelo
    que no sabe cuánto queda gasta como si no acabase nunca."""
    lineas = [f"Caso {t.procedencia.caso}. Te lo pasa {t.de} "
              f"porque {t.procedencia.motivo}.",
              f"Tu encargo: {t.encargo}",
              f"Tu autoridad: {t.autoridad}. Herramientas: "
              f"{', '.join(t.herramientas) or 'ninguna'}.",
              f"Quedan {t.presupuesto.saltos} saltos y "
              f"{t.presupuesto.eur:.2f} EUR en este caso."]
    lineas += [f"Ya establecido por {h}" for h in t.hechos]
    lineas += [f"Sigue abierto: {q}" for q in t.abiertas]
    return "\n".join(lineas)
