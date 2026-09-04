#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generar_env.py --- escribe banco/.env.example desde el libro.

El bloque `.env` del 0.4 es la fuente. Este script lo localiza por su
primera variable, vacia los valores que son marcadores y deja los que
son un valor de verdad (`ENTORNO=dev`, `LANGSMITH_TRACING=true`), y
escribe banco/.env.example. Ni una variable se escribe a mano.

Y la segunda mitad, que es la que impide la desincronizacion: toda
variable que banco/ lee con os.environ tiene que estar en ese bloque.
Si falta una, esto sale con 1 y la nombra --- el fichero que se importa
y muere en su primera linea no es un fichero entregado.

    generar_env.py                # genera
    generar_env.py --verificar    # solo compara, no escribe

Salidas: 0 correcto; 1 el libro se movio, falta una variable o el
fichero generado no coincide con el libro.
"""

import argparse
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
LIBRO = AQUI / ".." / ".." / ".." / "fuente" / "libro.md"
BANCO = AQUI / ".." / ".." / "banco"
PRIMERA = "OPENAI_API_BASE="        # la primera linea del bloque del 0.4
MARCADORES = ("...", "<")           # un valor con esto no es un valor
COLUMNA = 41                        # donde se alinea el comentario
AJENOS = (".venv", "venv", "__pycache__", ".pytest_cache",
          ".git", "site-packages")

USO = re.compile(
    r'os\.(?:environ\[|environ\.get\(|getenv\()["\']([A-Z0-9_]+)["\']')

CABECERA = """\
# .env.example --- GENERADO desde el bloque `.env` del 0.4 de libro.md
# por tools/generar_env/generar_env.py. NO editar a mano: si falta una
# variable se anade en el libro y se vuelve a generar.
#
# Copia a .env y rellena. El .env no entra en el repo jamas, y en este
# fichero no hay ni un secreto: los valores que quedan puestos son los
# que el libro da como valor y no como marcador.
#
# El codigo no conoce proveedores de modelos, solo conoce tu gateway
# (0.4). Cambiar de modelo es configuracion de LiteLLM, no un
# despliegue.
"""


def bloque_env(texto: str) -> list[str]:
    """Las lineas del bloque ini del 0.4, sin las vallas."""
    lineas = texto.splitlines()
    encontrados = []
    for i, linea in enumerate(lineas):
        if not linea.startswith(PRIMERA):
            continue
        j = i
        while j > 0 and not lineas[j - 1].startswith("```"):
            j -= 1
        if not lineas[j - 1].startswith("``` ini"):
            continue
        k = i
        while k < len(lineas) and not lineas[k].startswith("```"):
            k += 1
        encontrados.append(lineas[j:k])
    if len(encontrados) != 1:
        salir(f"el bloque `.env` del 0.4 no esta una sola vez en el "
              f"libro: {len(encontrados)} coincidencias de {PRIMERA!r}")
    return encontrados[0]


def salir(motivo: str) -> None:
    print(f"FALLO: {motivo}", file=sys.stderr)
    sys.exit(1)


def variable(linea: str) -> str:
    """El nombre de la variable de una linea, o '' si es comentario."""
    if linea.startswith("#") or "=" not in linea:
        return ""
    return linea.split("=", 1)[0]


def convertir(linea: str) -> str:
    """Vacia el valor si es marcador y realinea su comentario."""
    if not variable(linea):
        return linea
    izq, _, der = linea.partition("=")
    valor, sep, comentario = der.partition("#")
    valor = valor.rstrip()
    if any(m in valor for m in MARCADORES):
        valor = ""
    salida = f"{izq}={valor}"
    if sep:
        hueco = max(COLUMNA - len(salida), 2)
        salida = salida + " " * hueco + "#" + comentario.rstrip()
    return salida


def usadas(raiz: pathlib.Path) -> dict[str, str]:
    """Cada variable que banco/ lee, con el primer sitio donde la lee."""
    donde: dict[str, str] = {}
    for py in sorted(raiz.rglob("*.py")):
        if any(parte in AJENOS for parte in py.parts):
            continue
        texto = py.read_text("utf-8", errors="replace")
        for n, linea in enumerate(texto.splitlines(), 1):
            for nombre in USO.findall(linea):
                donde.setdefault(nombre, f"{py.relative_to(raiz)}:{n}")
    return donde


def render(lineas: list[str]) -> str:
    return CABECERA + "\n" + "\n".join(convertir(l) for l in lineas) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--libro", default=str(LIBRO))
    p.add_argument("--banco", default=str(BANCO))
    p.add_argument("--verificar", action="store_true")
    args = p.parse_args()

    libro = pathlib.Path(args.libro)
    banco = pathlib.Path(args.banco)
    if not libro.is_file():
        salir(f"no encuentro el libro en {libro}")
    if not banco.is_dir():
        salir(f"no encuentro el arbol en {banco}")

    lineas = bloque_env(libro.read_text("utf-8"))
    declaradas = {v for v in (variable(l) for l in lineas) if v}
    faltan = {n: d for n, d in usadas(banco).items()
              if n not in declaradas}
    for nombre in sorted(faltan):
        print(f"FALTA EN EL LIBRO: {nombre} --- lo lee "
              f"banco/{faltan[nombre]}", file=sys.stderr)

    texto = render(lineas)
    destino = banco / ".env.example"
    largas = [l for l in texto.splitlines() if len(l) > 78]
    if largas:
        salir(f"{len(largas)} lineas del bloque pasan de 78 columnas: "
              f"{largas[0]!r}")

    if args.verificar:
        actual = destino.read_text("utf-8") if destino.is_file() else ""
        if actual != texto:
            salir(f"{destino.name} no coincide con el libro: vuelve a "
                  f"ejecutar generar_env.py sin --verificar")
        if faltan:
            return 1
        print(f"OK: {len(declaradas)} variables, {destino.name} al dia "
              f"y ni una os.environ sin declarar")
        return 0

    destino.write_text(texto, encoding="utf-8")
    print(f"escrito {destino} --- {len(declaradas)} variables "
          f"desde el 0.4")
    if faltan:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
