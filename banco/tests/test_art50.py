# tests/test_art50.py --- la `prueba` que la ficha de arriba
# cita. Sin este fichero, el aserto de `test_conformidad` no
# falla por la razón que busca: muere con FileNotFoundError.
from cumplimiento import AVISOS


def test_las_cuatro_superficies():
    assert set(AVISOS) == {"chat", "slack", "voz", "avatar"}
    assert AVISOS["slack"] == AVISOS["chat"]
    assert all("inteligencia artificial" in t
               or "no es una persona" in t
               for t in AVISOS.values())


# tests/test_registro.py --- la de `art12_registro`, y comprueba
# el `rowcount`, porque la excepción no llega: con la RLS forzada
# del 16.6, el UPDATE y el DELETE se ejecutan y afectan a cero
# filas. Va con el rol `banco_app` de allí, nunca con el
# superusuario que trae por defecto tu portátil, porque
# BYPASSRLS se salta la RLS entera. Y contra una base de
# pruebas: la fila que deja no la borra nadie, que es justo lo
# que el test viene a demostrar.
import os

import psycopg

from cumplimiento import anotar


def test_solo_anadir():
    with psycopg.connect(os.environ["DATABASE_URL_APP"]) as bd:
        cur = bd.cursor()
        anotar("art50_aviso", "chat", "C-99", cur=cur)
        for sql in ("UPDATE banco.registro_ia SET canal = 'voz'",
                    "DELETE FROM banco.registro_ia"):
            cur.execute(f"{sql} WHERE sujeto = 'C-99'")
            assert cur.rowcount == 0


# --- anadido del M16.7 (extraer_banco) ---
# Anadido del M16.7.
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
