#!/usr/bin/env python3
"""integridad --- comprueba que cada bloque declarado es su bloque ENTERO.

POR QUE EXISTE, y es la tercera vez que este proyecto aprende la misma leccion.
El paquete tenia tres verificadores y los tres daban verde sobre un arbol roto:

  - `extraer_banco.py --verificar` comprueba que las anclas siguen donde estaban,
    no que el fichero extraido sea el bloque completo.
  - `cobertura.py` pregunta si todo bloque del libro tiene destino, no si el
    destino se lleva todo el bloque.
  - el `compileall` del CI pasa, porque medio fichero suele ser Python valido.

Con eso, ocho ficheros salieron truncados y nadie se entero: `agente_backoffice.py`
con 6 lineas de 101, `trocear.py` con 103 de 199 --- sin `trocear` ni `documentos`,
que son sus dos funciones publicas ---, y `politica.py` cortado a mitad de
`_limite_economico`, sin el `autorizar` que el resto del libro importa.

LA CAUSA. `resincronizar.py` localiza el fin de un bloque buscando su ancla de fin
hacia delante, y si esa linea aparece tambien a mitad del bloque, para alli. Un
ancla de fin desplazada corta el fichero por donde no toca.

QUE COMPRUEBA ESTO. En Markdown un bloque de codigo esta delimitado por sus vallas,
asi que el rango correcto no es una cuestion de anclas: es aritmetica. Todo rango
declarado tiene que ir de la primera a la ultima linea de contenido de su valla.

    python3 integridad.py --libro ../../fuente/libro.md [--arreglar]
"""
import argparse
import pathlib
import sys

import yaml


def vallas(lineas):
    """[(primera linea de contenido, ultima)] por cada bloque cercado."""
    out, abierta = [], None
    for n, l in enumerate(lineas, 1):
        if not l.startswith("```"):
            continue
        if abierta is None:
            abierta = n
        else:
            out.append((abierta + 1, n - 1))
            abierta = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--libro", required=True)
    ap.add_argument("--mapeo", default=str(pathlib.Path(__file__).parent / "mapeo.yaml"))
    ap.add_argument("--arreglar", action="store_true",
                    help="ajusta los rangos a su valla y reescribe mapeo.yaml")
    a = ap.parse_args()

    lineas = pathlib.Path(a.libro).read_text(encoding="utf-8").split("\n")
    caja = vallas(lineas)
    mapa = pathlib.Path(a.mapeo)
    m = yaml.safe_load(mapa.read_text(encoding="utf-8"))

    def contiene(n):
        for ini, fin in caja:
            if ini <= n <= fin:
                return (ini, fin)
        return None

    total, malos, parciales = 0, [], []
    for e in m["entradas"]:
        for r in e.get("bloques", []):
            total += 1
            # Un corte deliberado de un bloque mayor --- el de `nano_agent.py`
            # alimenta dos ficheros --- se declara, y asi no puede esconderse
            # detras de un rango que parece corto por descuido.
            if e.get("parcial"):
                parciales.append((e["destino"], str(r)))
                continue
            ini, fin = (int(x) for x in str(r).split("-"))
            real = contiene(ini)
            if real is None:
                malos.append((e["destino"], str(r), None, 0))
            elif (ini, fin) != real:
                malos.append((e["destino"], str(r), f"{real[0]}-{real[1]}",
                              (real[1] - real[0]) - (fin - ini)))

    print(f"  {total} bloques declarados en el mapeo")
    if parciales:
        print(f"  {len(parciales)} declarados `parcial: true`, y por eso no se exigen enteros:")
        for destino, r in parciales:
            print(f"    - {destino}: {r}")
    if not malos:
        print("  integridad completa: cada rango es su bloque entero.")
        return 0

    print(f"\n  {len(malos)} RANGOS QUE NO SON SU BLOQUE ENTERO:")
    for destino, r, real, faltan in sorted(malos, key=lambda x: -x[3]):
        if real is None:
            print(f"    - {destino}: {r} no cae dentro de ninguna valla")
        else:
            print(f"    - {destino}: declara {r} y su valla es {real}"
                  f"  ({faltan:+d} lineas)")

    if not a.arreglar:
        print("\n  El fichero extraido sale TRUNCADO y los otros verificadores no lo ven:")
        print("  las anclas siguen en su sitio y medio fichero es Python valido.")
        print("  Vuelve con --arreglar y revisa el diff.")
        return 1

    txt = mapa.read_text(encoding="utf-8")
    for destino, r, real, _ in malos:
        if real is None:
            continue
        txt = txt.replace(f"[{r}]", f"[{real}]", 1)
        txt = txt.replace(f"{r},", f"{real},", 1)
        txt = txt.replace(f" {r}]", f" {real}]", 1)
    mapa.write_text(txt, encoding="utf-8")
    print(f"\n  mapeo.yaml reescrito: {len(malos)} rangos ajustados a su valla.")
    print("  Extrae y COMPRUEBA QUE EL PYTHON COMPILA Y QUE LOS IMPORTS RESUELVEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
