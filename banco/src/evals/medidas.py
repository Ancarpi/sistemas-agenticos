# evals/medidas.py --- el evaluador del banco, y el fichero que
# el aceptacion.py del 31.2 importa. Tres piezas: el conjunto
# dorado versionado, la fila con los seis campos del 15.6, y el
# tercer veredicto.
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from random import Random

# Relativo a la raíz del repo, que es desde donde se lanza la
# corrida: un Path que en CI resuelve a otro sitio tumba la noche.
CONJUNTOS = Path("evals")
PROCEDENCIA: set[str] = set()   # lo que la corrida abrió DE VERDAD


def cargar(nombre: str, version: str, n: int,
           semilla: int) -> list[dict]:
    """El conjunto dorado, muestreado igual en tu portátil y en CI.
    Dos reglas que parecen burocracia y no lo son. La versión va en
    el NOMBRE del fichero y un fichero publicado no se edita:
    añadir un caso al final cambia la muestra ENTERA con la misma
    semilla, y tu serie histórica deja de comparar. Y el sha viaja
    con el resultado, porque «v3» es una promesa y el sha, la
    prueba."""
    ruta = CONJUNTOS / f"{nombre}.{version}.jsonl"
    crudo = ruta.read_bytes()
    casos = [json.loads(l) for l in crudo.splitlines() if l.strip()]
    if len(casos) < n:
        raise ValueError(f"{ruta.name}: {len(casos)} casos, "
                         f"pides {n}")
    sha = hashlib.sha256(crudo).hexdigest()[:12]
    PROCEDENCIA.add(f"{nombre}.{version}@{sha}")
    return Random(semilla).sample(casos, n)


def margen(p: float, n: int) -> float:
    """Cuánto mueve el puro azar del muestreo a una fracción p
    medida sobre n casos, al 95%. El suelo de 0,01 mantiene honesta
    la columna de ruido cuando p llega a 1: sin él la fórmula da
    cero y cuarenta casos sin una sola fuga se imprimirían como una
    medida exacta."""
    return 1.96 * math.sqrt(max(p * (1 - p), 0.01) / n)


def casos_para(caida: float, p: float = 0.8) -> int:
    """El inverso exacto de `margen`: los casos con los que
    el semiancho del intervalo al 95% vale `caida`.
    Cuadrática: para estrechar el intervalo a la mitad,
    cuatro veces los casos. casos_para(0,05) sobre 0,8 son
    246. Esta es la cifra del tercer veredicto, la que
    cierra un NO CONCLUYENTE. Cazar una caída es otra
    pregunta, y la contesta la función de abajo."""
    return math.ceil((1.96 / caida) ** 2 * p * (1 - p))


def casos_para_detectar(caida: float, p: float = 0.8,
                        caida_real: float = 0.0,
                        potencia: float = 0.9) -> int:
    """Los casos con los que `medir` dice FALLA, con esa
    probabilidad, cuando la caída ya ha ocurrido. Mira la
    regla entera, con el suelo dentro, y por eso empieza con
    un `raise`: ese suelo nunca baja de `caida_real`, así que
    una puerta que declara real la misma caída que sale a
    cazar acierta la mitad de las veces por muchos casos que
    le echen. `caida_real` va DEBAJO de lo que detectas."""
    if caida_real >= caida:
        raise ValueError(
            f"caida_real {caida_real} no baja de caida "
            f"{caida}: el suelo se come el veredicto y no "
            "hay n que lo arregle")
    sigma = math.sqrt(max((p - caida) * (1 - p + caida), 0.01))
    z = statistics.NormalDist().inv_cdf(potencia)
    # Manda el intervalo mientras `caida_real` quepa debajo
    # de él; en cuanto asoma, manda `caida_real` y la n se
    # dispara. Con 0,92, dos puntos y medio punto de suelo,
    # 2.365 casos para nueve de cada diez.
    t = (z + 1.96) / caida
    if caida_real * t > 1.96:
        t = z / (caida - caida_real)
    return math.ceil((sigma * t) ** 2)


@dataclass(frozen=True)
class Puerta:
    metrica: str
    medida: object       # una función (n, corpus, semilla) -> float
    casos: int
    umbral: float
    pases: int
    caida_real: float    # la caída que TÚ declaras real (18.4)
    # El orden es el de la tupla del 31.2 a propósito: allí las
    # seis puertas ya están escritas así y `Puerta(n, *p, RUIDO)`
    # las envuelve sin tocar el dict. Falta el segundo campo del
    # 15.6 --- conjunto y versión ---: lo pone `cargar` al abrir el
    # fichero, porque un campo de procedencia que se teclea miente.


def medir(p: Puerta, corpus: str, semilla: int) -> str:
    PROCEDENCIA.clear()
    v = sorted(p.medida(p.casos, corpus, semilla)
               for _ in range(p.pases))
    media, lo, hi = statistics.fmean(v), v[0], v[-1]
    # El suelo de ruido es el MAYOR de los tres, no el que más
    # convenga. La dispersión entre pases mide el ruido de
    # ejecución, y con un solo pase --- la excepción del 18.4 ---
    # es cero: una fila de un pase parece concluyente siempre. El
    # de muestreo no mira los pases, solo n.
    suelo = max(hi - lo, margen(media, p.casos), p.caida_real)
    if p.umbral >= 1.0:
        # Tolerancia cero: aquí no se estima una proporción, se
        # comprueba una existencia. Una fuga es una fuga y no hay
        # intervalo que discutir (el red team del 18.4).
        veredicto = "PASA" if media >= 1.0 else "FALLA"
    elif abs(media - p.umbral) < suelo:
        # La fila que casi nadie escribe: ni aprobado con reservas
        # ni suspenso, no hay medida. Lo que toca es ampliar la
        # muestra, y `casos_para` dice cuánto.
        veredicto = "NO CONCLUYENTE"
    else:
        veredicto = "PASA" if media >= p.umbral else "FALLA"
    # La fila entera, y la procedencia debajo: no caben juntas.
    print(f"{p.metrica:<16}{media:.3f} [{lo:.3f}-{hi:.3f}]"
          f" n={p.casos} x{p.pases} min={p.umbral:.2f}"
          f" +-{suelo:.3f}  {veredicto}\n"
          f"{'':16}{' '.join(sorted(PROCEDENCIA))}")
    return veredicto


# --- anadido del M15.7 (extraer_banco) ---
# Anadido del M15.7.
# evals/medidas.py (sigue) --- la medida determinista, la única
# que corre a un solo pase, y el juez, que no es ninguna de las
# seis puertas y es de quien cuelga todo lo que mide calidad.
from pydantic import BaseModel, Field

from src.core.models import get_model     # la fábrica del 0.4
from src.rag.rerank import recuperar      # el retriever del 8.2

# El juez no puede ser el juzgado: `agente-listo` es el alias con
# el que responde el agente, así que el juez usa el de OTRO
# proveedor (0.5) --- y si aquél cae en su fallback, vuelven a
# coincidir. Cambiar `VERSION_JUEZ` rompe la serie histórica: se
# cambia el día que lo recalibras a mano contra tus etiquetas.
JUEZ = "agente-listo-backup"
VERSION_JUEZ = "2026-09-a"
# Toda medida recibe `corpus` y ninguna busca con él: la colección
# del 24.1 la fija el índice ya cargado, y el argumento está para
# que el encabezado del 31.2 no pueda nombrar un corpus mientras
# la medida corre contra otro.


def recall_at_k(orden: list[str],
                correctas: set[str], k: int = 5) -> float:
    """Cuántos de los documentos correctos caen en el top k. La
    definición vive aquí y en ningún otro sitio: el
    `run_rag_eval.py` del 8.3 tenía la suya, con otra aritmética
    y otro conjunto, y dos definiciones de una métrica son una
    métrica y un error esperando su turno."""
    return len(correctas & set(orden[:k])) / len(correctas)


def recall5(n: int, corpus: str, semilla: int) -> float:
    """Determinista sobre índice congelado: de ahí el pase único
    del 18.4. Y de ahí también que su fila sea la que obliga a que
    el suelo de `medir` no sea solo la dispersión. Recupera con
    el `nivel` de cada caso y no como dueño de la tabla: la RLS
    del 7.6 cambia el corpus, y un recall medido sin ella mide un
    sistema que nadie despliega. Y la serie no se mueve al pasar
    a `recall_at_k`: con un documento correcto por caso, contar
    aciertos y promediar recalls dan el mismo número."""
    casos = cargar("rag_dataset", "v3", n, semilla)
    logrado = sum(
        recall_at_k([t["meta"]["fuente"] for t in
                     recuperar(c["pregunta"], niveles=c["nivel"])],
                    set(c["fuentes"])) for c in casos)
    return logrado / n


class Fundamento(BaseModel):
    correcta: bool = Field(
        description="Coincide con la respuesta de referencia")
    fundamentada: bool = Field(
        description="Toda afirmación se apoya en el contexto")
    motivo: str = Field(description="Una frase, citando el trozo")


def juzga(pregunta: str, contexto: str, referencia: str,
          respuesta: str) -> Fundamento:
    """Booleanos, nunca un 1-10: una escala que el juez no sabe
    anclar devuelve 7 casi siempre, y el 7 no es una medida. El
    `contexto` es el RECUPERADO, no el del conjunto dorado: aquí
    se mide si la respuesta se apoya en lo que el sistema leyó, no
    en lo que debería haber leído; eso es `recall5`, y es otra
    puerta. Y el `run_name` no es adorno: sin él, la traza del
    15.1 tiene mil llamadas al juez y ninguna atribuible."""
    modelo = get_model(JUEZ).with_structured_output(Fundamento)
    return modelo.invoke(
        f"Pregunta: {pregunta}\n\nContexto:\n{contexto}\n\n"
        f"Referencia:\n{referencia}\n\nRespuesta:\n{respuesta}\n\n"
        "¿Se apoya la respuesta SOLO en el contexto y coincide con "
        "la referencia? No premies la longitud ni el estilo.",
        config={"run_name": f"juez.{VERSION_JUEZ}",
                "metadata": {"juez": VERSION_JUEZ}})
