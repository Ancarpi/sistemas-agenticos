# tests/test_art50.py --- el `prueba` que el YAML cita para
# `art50_aviso`. Ni modelo ni base de datos: lo que se comprueba
# es el texto y quién lo tiene.
from cumplimiento import AVISOS, VERSION_AVISO


def test_las_cuatro_superficies():
    assert set(AVISOS) == {"chat", "slack", "voz", "avatar"}
    # El backend no lleva aviso: nadie humano lee su salida en
    # el momento, y su obligación es la fila del 26(11).
    assert "backend" not in AVISOS
    assert AVISOS["slack"] is AVISOS["chat"]   # el texto, no el canal
    for texto in AVISOS.values():
        assert "artificial" in texto or "automático" in texto
    assert "graba" in AVISOS["voz"]
    assert "cara" in AVISOS["avatar"]          # el marcado del 50(2)
    assert len(VERSION_AVISO) == 10            # una fecha, no un «v1»
