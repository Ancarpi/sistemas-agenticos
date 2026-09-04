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
# abre frase. El `0-9` que llevaba el lookahead está fuera, y por
# lo que rompía: con él «el Art. 50(2)» se parte en dos y «las
# filas del Art. 26(11) y del Art. 14.» en tres, sobre un corpus
# que es el manual normativo de un banco. Se paga con lo
# contrario: la frase que de verdad empieza por una cifra, o el
# número de una lista, ya no separa. Si tu corpus vive de esas
# listas, la alternativa es un lookbehind de abreviaturas
# (`art`, `núm`, `pág`) en vez de la clase de la derecha.
FRASE = re.compile(r"(?<=[.!?:])\s+(?=[«\"(¿¡A-ZÁÉÍÓÚÑ])")
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "banco.manuales")


def cabecera(titulos: str, meta: dict) -> str:
    """El «[fuente · títulos]» que `trozo` mete DENTRO del texto.

    Vive aparte porque la miran dos: `trozo` para escribirla y
    `trocear` para descontar su longitud del tope antes de
    empaquetar. Y recorta a 200 igual que `seccion`, así que el
    metadato describe lo que de verdad se embebió."""
    t = titulos[:200]
    return f"[{meta['fuente']} · {t}]\n" if t else ""


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


def trozo(titulos: str, texto: str, meta: dict) -> dict:
    # El título va DENTRO del texto que se embebe, no solo en el
    # metadato: «será del 0,50%» no lo recupera ninguna consulta,
    # porque no contiene ninguna de sus palabras. Es la mitad
    # barata del enriquecido, y no cuesta una llamada.
    cabeza = cabecera(titulos, meta)
    t = {**meta, "content": cabeza + texto,
         "seccion": titulos[:200] or None}
    # uuid5 del contenido: reindexar SOBRESCRIBE, no duplica, que
    # es el criterio del Ejercicio 7.1. Tiene precio: si tocas el
    # partidor cambian todos los ids y el corpus viejo se queda
    # al lado del nuevo. Reindexado entero, o DELETE por fuente.
    t["langchain_id"] = str(
        uuid.uuid5(NS, meta["fuente"] + "|" + t["content"]))
    return t


def trocear(texto: str, meta: dict, tope: int = TOPE,
            solape: int = SOLAPE) -> list[dict]:
    """Estructura-consciente: el de partida, y casi siempre el
    definitivo. Cero llamadas al modelo para indexar."""
    return [trozo(titulos, parte, meta)
            for titulos, cuerpo in secciones(texto)
            # La cabeza se embebe con el texto, así que sale
            # del mismo presupuesto: sin descontarla, una
            # sección de títulos largos entrega trozos por
            # encima del tope y el modelo los trunca en silencio.
            for parte in empaquetar(
                frases(cuerpo),
                tope - len(cabecera(titulos, meta)), solape)]


def documentos(trozos: list[dict]) -> list[Document]:
    """El puente al `add_documents` del 7.4, que quiere `Document`
    y no dicts. El `langchain_id` del uuid5 viaja como `id`, y por
    ahí reindexar sobrescribe en vez de duplicar; el resto del
    dict va a `metadata`, que son las columnas del 7.6."""
    fuera = ("content", "langchain_id")
    return [Document(id=t["langchain_id"], page_content=t["content"],
                     metadata={k: v for k, v in t.items()
                               if k not in fuera})
            for t in trozos]


def coseno(a: list[float], b: list[float]) -> float:
    p = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return p / (na * nb) if na and nb else 0.0


def cortes(bloques: list[tuple[str, list[str]]],
           percentil: int) -> set[tuple[int, int]]:
    """Los cortes (bloque, frase) donde cambia el significado.

    El umbral sale del documento ENTERO y las distancias se miden
    solo dentro de cada sección. Sacar el percentil sección a
    sección no funciona: una de diez frases deja nueve distancias
    y el 95 de nueve no corta jamás. Y las parejas que cruzan un
    encabezado no entran, porque ese corte ya lo puso el autor.
    """
    if sum(len(fs) - 1 for _, fs in bloques) < 20:
        return set()          # sin muestra no hay percentil
    v = get_embeddings().embed_documents(
        [f for _, fs in bloques for f in fs])     # UNA llamada
    dist: dict[tuple[int, int], float] = {}
    base = 0
    for b, (_, fs) in enumerate(bloques):
        for j in range(len(fs) - 1):
            dist[(b, j + 1)] = 1 - coseno(v[base + j],
                                          v[base + j + 1])
        base += len(fs)
    umbral = quantiles(list(dist.values()), n=100)[percentil - 1]
    return {k for k, d in dist.items() if d > umbral}


def trocear_semantico(texto: str, meta: dict, tope: int = TOPE,
                      percentil: int = PERCENTIL) -> list[dict]:
    """Igual, pero cortando donde cambia el significado.

    Corre DENTRO de cada sección, nunca por encima: un corte que
    fusiona dos encabezados deja un trozo cuyo metadato `seccion`
    miente, y con él la cita que el 7.5 promete al auditor. Y sin
    solape, porque el solape devolvería al trozo justo la frase
    que el corte acaba de declarar de otro tema.
    """
    bloques = [(t, frases(c)) for t, c in secciones(texto)]
    marcas = cortes(bloques, percentil)
    salida: list[dict] = []
    for b, (titulos, fs) in enumerate(bloques):
        # La cabeza sale del mismo presupuesto que en `trocear`.
        hueco = tope - len(cabecera(titulos, meta))
        grupo: list[str] = []
        for j, frase in enumerate(fs):
            if (b, j) in marcas and grupo:
                salida += [trozo(titulos, p, meta)
                           for p in empaquetar(grupo, hueco, 0)]
                grupo = []
            grupo.append(frase)
        salida += [trozo(titulos, p, meta)
                   for p in empaquetar(grupo, hueco, 0)]
    return salida
