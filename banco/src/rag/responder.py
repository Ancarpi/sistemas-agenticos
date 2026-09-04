# src/rag/responder.py --- la tercera pieza del RAG: el prompt, el
# formato de cita y la comprobación de que la cita existe.
import re

from src.core.models import get_model        # la fábrica del 0.4
from src.rag.hibrida import NIVELES
from src.rag.rerank import AL_MODELO, recuperar

MODELO = "agente-listo"     # el alias del 0.5, nunca un proveedor
NO_CONSTA = "No consta en la documentación consultada."
CITA = re.compile(r"\[\[(\d{1,2})\]\]")

SISTEMA = """Eres el asistente documental de un banco.
Responde SOLO con lo que digan los trozos numerados de abajo.
Cierra cada afirmación con la marca del trozo que la sostiene, en
la forma [[3]]; si la sostienen dos trozos, [[1]][[4]].
Usa únicamente las marcas que aparecen abajo: no las agrupes en
rangos, no las inventes, y no completes con normativa que
recuerdes y no esté en los trozos.
Cantidades, plazos y códigos se copian literales del trozo.
Si los trozos no cubren la pregunta, responde exactamente
«{escape}», sin marcas y sin añadir nada más."""


def bloque(trozos: list[dict]) -> tuple[str, dict[str, dict]]:
    """El contexto numerado, y el mapa marca -> trozo.

    La marca es un ordinal de ESTA llamada y no el `langchain_id`:
    un uuid copiado por un modelo sale mal cada pocas veces, y un
    uuid mal copiado no se distingue de uno inventado. El id vive
    en el mapa, que es lo que acaba en el registro de auditoría.
    """
    mapa = {str(n): t for n, t in enumerate(trozos, start=1)}
    return "\n\n".join(
        f"[[{m}]] fuente: {t['meta']['fuente']} · sección: "
        f"{t['meta']['seccion'] or 'sin sección'}\n{t['content']}"
        for m, t in mapa.items()), mapa


def comprobar(texto: str, mapa: dict[str, dict]) -> list[str]:
    """Los defectos de citado, y aquí está el apartado entero.

    Sin estas líneas, «cita tus fuentes» es una frase del prompt:
    una respuesta que cierra con [[7]] sobre cinco trozos
    entregados pasa la revisión de la demo y llega al auditor con
    una fuente que no existe. Con ellas es un fallo que se cuenta.
    """
    marcas = CITA.findall(texto)
    defectos = [f"[[{m}]] no se pasó al modelo"
                for m in sorted(set(marcas)) if m not in mapa]
    if not marcas and texto.strip() != NO_CONSTA:
        # Ni una cita ni la salida de escape: la respuesta sale de
        # la memoria del modelo, que es lo que el RAG venía a
        # quitar. Es el más silencioso de los dos defectos, porque
        # el texto suele estar bien.
        defectos.append("respuesta sin ninguna cita")
    return defectos


def responder(pregunta: str, niveles: str = NIVELES) -> dict:
    """Recuperar, generar citando, y comprobar las citas antes de
    devolver nada. El nivel llega hasta aquí porque una respuesta
    no puede citar el trozo que el retriever del 8.2 ocultó."""
    trozos = recuperar(pregunta, niveles=niveles)[:AL_MODELO]
    if not trozos:
        return {"texto": NO_CONSTA, "citas": {}, "contexto": "",
                "defectos": []}
    contexto, mapa = bloque(trozos)
    texto = get_model(MODELO).invoke(
        [("system", SISTEMA.format(escape=NO_CONSTA)),
         ("human", f"Pregunta: {pregunta}\n\n{contexto}")],
        config={"run_name": "rag.responder"}).content.strip()
    citas = {m: {"id": t["id"], "fuente": t["meta"]["fuente"],
                 "seccion": t["meta"]["seccion"]}
             for m, t in mapa.items() if f"[[{m}]]" in texto}
    salida = {"texto": texto, "citas": citas, "contexto": contexto,
              "defectos": comprobar(texto, mapa)}
    if salida["defectos"]:
        # La respuesta no se reescribe: se retira. Un reintento con
        # el mismo prompt gasta otra llamada y vuelve a inventar
        # con la misma probabilidad, y lo que hay que saber es cada
        # cuánto pasa. Eso lo cuenta la puerta del 8.3.
        salida["rechazada"] = texto
        salida["texto"], salida["citas"] = NO_CONSTA, {}
    return salida


if __name__ == "__main__":
    import sys

    r = responder(sys.argv[1], niveles="publica,interna")
    print(r["texto"], "\n")
    for m, c in sorted(r["citas"].items()):
        print(f"[[{m}]] {c['fuente']} · {c['seccion']}  {c['id']}")
    for d in r["defectos"]:
        print(f"DEFECTO  {d}")
    sys.exit(1 if r["defectos"] else 0)
