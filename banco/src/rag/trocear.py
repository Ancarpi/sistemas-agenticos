# src/rag/trocear.py --- el partidor del corpus del 7.6: por
# estructura, y la variante semántica sobre la misma base.
import re
import uuid
from statistics import quantiles

from langchain_core.documents import Document

from src.core.models import get_embeddings   # la fábrica del 0.4

# El tope no lo eliges tú: lo impone el modelo detrás del alias
# emb-multilingue, que en el 0.5 es cohere/embed-multilingual-v3.0
# y trunca en silencio a 512 tokens lo que le sobre. De ahí el
# 450, que deja margen para la cabeza de títulos que pone `trozo`
# y para el error de la estimación: aquí se ESTIMA y allí se
# tokeniza, así que mide el ratio en tu corpus con el tokenizador
# real y bájalo si sale por debajo. Tampoco esperes que la
# librería lo pare: `get_embeddings` pasa
# `check_embedding_ctx_length=False` (0.4). Un trozo truncado no
# da error: da el vector de medio párrafo con los metadatos del
# párrafo entero.
TOPE_TOKENS = 450
CHARS_POR_TOKEN = 3.0
TOPE = int(TOPE_TOKENS * CHARS_POR_TOKEN)
SOLAPE = 2        # frases del trozo anterior que se repiten
PERCENTIL = 95    # el umbral del semántico; se mueve con el 8.3

TITULO = re.compile(r"^(#{1,6})\s+(.+)$")
VALLA = re.compile(r"^\s*(```|~~~)")
# Corta tras punto, cierre o dos puntos, y solo si lo que sigue
# abre frase. Sin el lookahead, «art. 66.1.b)» son tres frases.
FRASE = re.compile(r"(?<=[.!?:])\s+(?=[«\"(¿¡A-ZÁÉÍÓÚÑ0-9])")
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "banco.manuales")


def secciones(texto: str) -> list[tuple[str, str]]:
    """(jerarquía de títulos, cuerpo) por cada encabezado.

    La valla de código se cuenta a propósito: dentro de un
    bloque vallado, una línea que empieza por # es un comentario
    y no un encabezado, y partir por ahí trocea justo el ejemplo
    que el lector iba a copiar.
    """
    pila: list[str] = []
    cuerpo: list[str] = []
    salida: list[tuple[str, str]] = []
    dentro = False
    for linea in texto.splitlines():
        if VALLA.match(linea):
            dentro = not dentro
        cabecera = None if dentro else TITULO.match(linea)
        if cabecera is None:
            cuerpo.append(linea)
            continue
        if any(c.strip() for c in cuerpo):
            salida.append((" > ".join(pila), "\n".join(cuerpo)))
        nivel = len(cabecera.group(1))
        pila = pila[:nivel - 1] + [cabecera.group(2).strip()]
        cuerpo = []
    if any(c.strip() for c in cuerpo):
        salida.append((" > ".join(pila), "\n".join(cuerpo)))
    return [(t, c.strip()) for t, c in salida]


def frases(cuerpo: str) -> list[str]:
    return [f.strip() for f in FRASE.split(cuerpo) if f.strip()]


def empaquetar(piezas: list[str], tope: int,
               solape: int) -> list[str]:
    """Agrupa frases hasta el tope arrastrando `solape` de ellas.

    El solape se mide en frases y no en caracteres: cortar a 150
    caracteres parte una palabra y deja media en cada trozo. La
    primera línea es la red de seguridad, porque una tabla de
    doscientas filas llega aquí como UNA pieza.
    """
    piezas = [x[i:i + tope] for x in piezas
              for i in range(0, max(len(x), 1), tope)]
    salida: list[str] = []
    actual: list[str] = []
    largo = 0
    for pieza in piezas:
        if actual and largo + len(pieza) > tope:
            salida.append(" ".join(actual))
            # El arrastre no puede comerse el trozo siguiente: con
            # frases largas `actual[-solape:]` ya ocupa el tope y
            # el trozo que viene sale con más solape que contenido.
            actual = actual[-solape:] if solape else []
            while sum(len(p) + 1 for p in actual) > tope // 2:
                actual.pop(0)
            largo = sum(len(p) + 1 for p in actual)
            # Y el arrastre cede ante el tope, que es lo que
            # faltaba: el flush ocurre ANTES de añadir la pieza,
            # así que con una pieza que ya roza el límite el trozo
            # salía por encima del tope que acabas de fijar.
            while actual and largo + len(pieza) > tope:
                largo -= len(actual.pop(0)) + 1
        actual.append(pieza)
        largo += len(pieza) + 1
    if actual:
        salida.append(" ".join(actual))
    return salida
