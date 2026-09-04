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
import re
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

    # LA GRIETA QUE ESTA COMPROBACION ABRIO, y merece quedar escrita porque es
    # la leccion mas incomoda del proyecto. Al exigir que cada rango sea su valla
    # entera, esta comprobacion OBLIGA a fusionar dos entregas que compartan
    # valla: la 5843 del libro imprimia `test_art50.py` y `test_registro.py`
    # dentro de la misma, y el fichero extraido se llevaba el otro dentro con dos
    # funciones tapandose. La comprobacion estrella producia el defecto que venia
    # a cerrar. Se arregla mirando si una cabecera de fichero aparece DENTRO de la
    # valla y no en su primera linea: eso son dos entregas y la valla hay que
    # partirla en el libro.
    # Una cabecera de entrega es la forma que el libro usa siempre: el comentario,
    # un espacio, la ruta y la raya. Un comentario que solo MENCIONA un fichero
    # («# evals/medidas.py del 15.7: cada funcion...») no abre una entrega, y sin
    # exigir la raya esta regla daba tres falsos positivos de cuatro.
    CABEZA = re.compile(
        r"^(?:#|--) (?!\s)([A-Za-z0-9_./-]+\.(?:py|sql|ya?ml|toml|sh)) ---")
    dobles = []
    for ini, fin in caja:
        dentro = [n for n in range(ini + 1, fin + 1) if CABEZA.match(lineas[n - 1])]
        if dentro:
            dobles.append((ini, fin, dentro))

    # Y la otra pregunta que ninguna comprobacion hacia: ¿se entrega alguna linea
    # del libro DOS VECES? `plataforma/runtime.py` declaraba el mismo rango en un
    # verbatim y en un patch, asi que el fichero se contenia a si mismo, 422
    # lineas donde el fichero son 264, con veintidos funciones redefinidas. Los
    # cuatro verificadores daban verde, y la prueba estaba impresa en pantalla
    # desde el primer dia: esta comprobacion contaba 101 bloques y `cobertura.py`
    # 100, porque aquella los mete en un `set()`. Ese uno de diferencia era el bug.
    from collections import Counter
    veces = Counter()
    for e in m["entradas"]:
        for r in e.get("bloques", []):
            veces[(e["destino"], str(r))] += 1
    repes = [(d, r, n) for (d, r), n in veces.items() if n > 1]

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
    if repes:
        print(f"\n  {len(repes)} RANGO(S) DECLARADO(S) MAS DE UNA VEZ --- el fichero se contiene a si mismo:")
        for d, r, n in repes:
            print(f"    - {d}: {r} declarado {n} veces")
    if dobles:
        print(f"\n  {len(dobles)} VALLA(S) CON DOS ENTREGAS --- no se pueden dar enteras a un destino:")
        for ini, fin, dentro in dobles:
            print(f"    - valla {ini}-{fin}: hay cabecera de fichero en {dentro}")
            print(f"      Partela en el libro en dos bloques, o declarala `parcial: true` con un rango por destino.")
    if parciales:
        print(f"  {len(parciales)} declarados `parcial: true`, y por eso no se exigen enteros:")
        for destino, r in parciales:
            print(f"    - {destino}: {r}")
    if not malos and not repes and not dobles:
        print("  integridad completa: cada rango es su bloque entero, ninguno")
        print("  se declara dos veces y ninguna valla lleva dos entregas.")
        return 0
    if not malos:
        return 1

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
