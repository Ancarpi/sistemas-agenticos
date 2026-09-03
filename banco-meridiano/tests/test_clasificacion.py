# tests/test_clasificacion.py --- lo que separa un control de un
# PDF con otra extensión. `safe_load` ya devuelve un `date`, así
# que la comparación de fechas es la que parece.
import pathlib
from datetime import date

import yaml

RUTA = pathlib.Path("compliance/clasificacion-ia.yaml")
DOC = yaml.safe_load(RUTA.read_text("utf-8"))


def test_conformidad():
    assert date.today() < DOC["proximo_examen"]
    for s in DOC["sistemas"]:
        for art, o in s["obligaciones"].items():
            if o.get("estado") != "implementado":
                continue
            # `prueba` también: un test renombrado envejece igual
            # de callado que un símbolo renombrado.
            for clave in ("evidencia", "prueba"):
                if clave not in o:
                    continue
                fich, _, simbolo = o[clave].partition("::")
                texto = pathlib.Path(fich).read_text("utf-8")
                assert simbolo in texto, f"{s['id']}/{art}"
