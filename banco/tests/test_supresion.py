# tests/test_supresion.py --- los dos casos negativos que el red
# team dejó sobre la supresión distribuida del 34.6. Tocan Postgres
# porque lo que se mide es el ALCANCE de los DELETE y el cierre de
# la cola del 35.6, no una línea de Python. A diferencia del test
# de RLS (16.7), que sin base de datos debe fallar, estos saltan
# limpio: miden código de aplicación, no una promesa del schema.
import os
import uuid

import psycopg
from psycopg.rows import dict_row
import pytest

# El cierre de pendientes firma el rechazo con la clave del broker
# (35.6). En un árbol recién clonado el `.env` la trae vacía; para
# medir la supresión vale cualquiera.
os.environ.setdefault("HITL_CLAVE", "clave-de-test")


def _bd():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("sin DATABASE_URL no hay supresión que medir")
    try:
        return psycopg.connect(url, autocommit=True,
                               row_factory=dict_row,
                               options="-c search_path=banco,public")
    except psycopg.OperationalError as e:
        pytest.skip("sin Postgres arriba: "
                    + str(e).splitlines()[0])


def test_guion_bajo_no_es_comodin():
    # `_` y `%` son comodines de LIKE y el sujeto viene de fuera:
    # sin escaparlos, suprimir C_1 barre el store de CX1 --- las
    # filas de OTRO cliente. El vecino difiere justo en la
    # posición del guion bajo, que es lo que un comodín pisaría.
    bd = _bd()
    from src.core.supresion import suprimir_sujeto
    suf = uuid.uuid4().hex[:8]
    sujeto, vecino = f"C_{suf}", f"CX{suf}"
    prefijos = [f"banco.preferencias.{s}" for s in (sujeto, vecino)]
    prefijos += [f"banco.soporte.{s}.notas" for s in (sujeto, vecino)]
    with bd, bd.cursor() as cur:
        cur.execute("SELECT to_regclass('store') IS NULL AS falta")
        creada = cur.fetchone()["falta"]
        if creada:
            # La crea el setup() del PostgresStore (6.2); si este
            # árbol aún no lo corrió, vale su forma mínima.
            cur.execute("CREATE TABLE store (prefix text NOT NULL,"
                        " key text NOT NULL, value jsonb)")
        try:
            for pre in prefijos:
                cur.execute("INSERT INTO store (prefix, key, value)"
                            " VALUES (%s, 'pref', '{}')", (pre,))
            suprimir_sujeto(sujeto, f"EXP-{suf}", "dpo:test")
            cur.execute("SELECT prefix FROM store WHERE prefix"
                        " = ANY(%s)", (prefijos,))
            quedan = sorted(f["prefix"] for f in cur.fetchall())
            # El sujeto cayó entero y el vecino sigue entero.
            assert quedan == sorted(p for p in prefijos
                                    if vecino in p)
        finally:
            cur.execute("DELETE FROM store WHERE prefix = ANY(%s)",
                        (prefijos,))
            if creada:
                cur.execute("DROP TABLE store")
            cur.execute("DELETE FROM banco.supresiones WHERE"
                        " solicitud = %s", (f"EXP-{suf}",))


def test_la_pendiente_se_cierra_antes_de_purgarse():
    # La purga del 34.7 vacía `propuesta`; una pendiente del sujeto
    # que SOLO se vaciara quedaría en la cola como `{}`, firmable a
    # ciegas. Primero se cierra (rechazo firmado por el sistema),
    # luego se redacta; y una purgada nunca se decide.
    bd = _bd()
    from src.core import hitl
    from src.core.supresion import suprimir_sujeto
    suf = uuid.uuid4().hex[:8]
    sujeto = f"C-{suf}"
    fila = hitl.encolar(hilo=f"caso:{sujeto}", run=f"r-{suf}",
                        agente={"id": "backoffice",
                                "version": "4.2"},
                        propone="human:u-31",
                        propuesta={"importe": 100},
                        accion="abrir_disputa", sujeto=sujeto)
    assert fila["estado"] == "pendiente"
    try:
        suprimir_sujeto(sujeto, f"EXP-{suf}", "dpo:test")
        with bd.cursor() as cur:
            cur.execute("SELECT estado, aprobador, propuesta,"
                        " firma, purgado_en FROM banco.aprobaciones"
                        " WHERE id = %s", (fila["id"],))
            f = cur.fetchone()
        assert f["estado"] == "rechazada"        # cerrada, no rota
        assert f["aprobador"] == "sistema:supresion"
        assert f["firma"] is not None            # receipt firmado
        assert f["propuesta"] == {}              # y luego purgada
        assert f["purgado_en"] is not None
        pendientes = [p["id"] for p in hitl.pendientes()]
        assert fila["id"] not in pendientes
        with pytest.raises(hitl.ReciboInvalido):
            hitl.aprobar(fila["id"], "human:u-99")
    finally:
        with bd, bd.cursor() as cur:
            cur.execute("DELETE FROM banco.aprobaciones WHERE"
                        " id = %s", (fila["id"],))
            cur.execute("DELETE FROM banco.supresiones WHERE"
                        " solicitud = %s", (f"EXP-{suf}",))
