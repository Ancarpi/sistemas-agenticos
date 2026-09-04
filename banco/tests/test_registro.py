# tests/test_registro.py --- el `prueba` de `art12_registro`.
# Este sí toca Postgres, porque lo que se comprueba es la RLS y
# no una línea de Python: UPDATE y DELETE tienen que salir SIN
# error y con cero filas afectadas. Con el `DATABASE_URL_APP` del
# `.env` del 0.4, que es el rol NOBYPASSRLS del 16.6: con un
# superusuario el test pasa en verde midiendo lo contrario de lo
# que dice medir.
import os
import uuid

import psycopg


def test_solo_anadir():
    sujeto = "prueba:" + uuid.uuid4().hex[:8]
    with psycopg.connect(os.environ["DATABASE_URL_APP"]) as bd:
        bd.execute("SET search_path = banco, public")
        bd.execute("INSERT INTO registro_ia (tipo, canal, sujeto)"
                   " VALUES ('art50_aviso', 'chat', %s)", (sujeto,))
        borra = bd.execute("DELETE FROM registro_ia"
                           " WHERE sujeto = %s", (sujeto,))
        assert borra.rowcount == 0      # sin error, y sin efecto
        toca = bd.execute("UPDATE registro_ia SET canal = 'voz'"
                          " WHERE sujeto = %s", (sujeto,))
        assert toca.rowcount == 0
        fila = bd.execute("SELECT canal FROM registro_ia"
                          " WHERE sujeto = %s", (sujeto,)).fetchone()
        assert fila == ("chat",)        # sigue ahí, y sin tocar
