# tests/test_integracion.py --- el humo de integración de la
# plataforma: hitl (35.6) + memoria (34.7) + supresión (34.6) +
# runtime (37.2), juntos y con UN solo sujeto. El recorrido es el
# del arbitraje que lo motivó: la memoria individual entra por la
# tool del 34.5, la colectiva se propone y se aprueba por la cola
# del 35.6, el `decidir` del 37.2 encola una propuesta con el
# `ctx["sujeto"]` con su clase (`cliente:C-99`), y la supresión
# tiene que barrerlo TODO --- las dos grafías del mismo sujeto ---
# y contarlo en el receipt. Toca Postgres porque lo que mide son
# las costuras entre módulos, no una línea de Python; sin base de
# datos salta limpio, como test_supresion.py.
import os
import sys
import types
import uuid

import psycopg
from psycopg.rows import dict_row
import pytest

os.environ.setdefault("HITL_CLAVE", "clave-de-test")
os.environ.setdefault("ENTORNO", "dev")


def _bd():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("sin DATABASE_URL no hay integración que medir")
    try:
        return psycopg.connect(url, autocommit=True,
                               row_factory=dict_row,
                               options="-c search_path=banco,public")
    except psycopg.OperationalError as e:
        pytest.skip("sin Postgres arriba: "
                    + str(e).splitlines()[0])


def _runtime():
    """Importa el runtime del 37.2 con sus hermanos de import en el
    path (README, nivel 2). `identidad` entra como doble mínimo: el
    fichero impreso del 18.3 lleva sus líneas de sustitución
    (`HILO = hilo(...)`, nombres de otros ficheros) y no se deja
    importar tal cual."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for d in ("src/agents", "src/agents/backoffice"):
        ruta = os.path.join(raiz, d)
        if ruta not in sys.path:
            sys.path.insert(0, ruta)
    if "identidad" not in sys.modules:
        ident = types.ModuleType("identidad")
        ident.GRAFOS = {"conciliacion", "voz"}
        ident.hilo = lambda g, s: f"{g}|{s}"
        ident.memoria = lambda s: tuple(s.split(":", 1))
        sys.modules["identidad"] = ident
    import runtime
    return runtime


class _Pausa(Exception):
    """El interrupt() del test: donde el grafo de verdad pausa."""


def test_un_sujeto_cruza_hitl_memoria_supresion_y_runtime():
    bd = _bd()
    from src.core import hitl, memoria
    from src.core.supresion import suprimir_sujeto
    rt = _runtime()

    suf = uuid.uuid4().hex[:8]
    sujeto = f"C-{suf}"                  # la grafía de las tools
    con_clase = f"cliente:{sujeto}"      # la del ctx del 37.2
    run, exp = f"run-{suf}", f"EXP-{suf}"
    hilo_rt = f"banco.sepa.backoffice|{con_clase}"
    ctx_viejo, aut_viejo, int_viejo = (memoria.CTX, rt.autorizar,
                                       rt.interrupt)
    ids_hitl, ref = [], None
    with bd.cursor() as cur:
        cur.execute("SELECT to_regclass('store') IS NULL AS falta")
        store_creada = cur.fetchone()["falta"]
        if store_creada:
            cur.execute("CREATE TABLE store (prefix text NOT NULL,"
                        " key text NOT NULL, value jsonb)")
    try:
        # 1. La traza que da procedencia (16.6) y la memoria
        #    INDIVIDUAL por la tool del 34.5, con la grafía que a
        #    veces teclea el modelo: la clase delante.
        with bd.cursor() as cur:
            cur.execute("INSERT INTO banco.registro_ia (tipo,"
                        " canal, sujeto, traza) VALUES"
                        " ('art26_decision', 'chat', %s, %s)",
                        (sujeto, run))
        with bd.cursor() as cur:
            # Lo que un agente escribió a pelo en el store del 6.2,
            # sin pasar por la API tipada: también es del sujeto.
            cur.execute("INSERT INTO store (prefix, key, value)"
                        " VALUES (%s, 'nota', '{}')",
                        (f"banco.soporte.{sujeto}",))
        memoria.CTX = lambda: {"run": run,
                               "humano": {"id": f"op-{suf}"},
                               "agente": {"id": "backoffice",
                                          "version": "4.2"}}
        rec = memoria.recordar_preferencia_cliente.func(
            cliente_id=con_clase, clave="idioma", valor="es",
            evidencia="lo declara en el turno 3 del hilo")
        assert rec.namespace == ("banco", "preferencias", sujeto), \
            "la tool no normalizó la grafía del modelo"

        # 2. La memoria COLECTIVA se propone (34.5) y la aprueba un
        #    steward por la cola del 35.6, que publica (34.7).
        prop = memoria.proponer_memoria_colectiva.func(
            dominio="sepa", tipo="faq",
            resumen="las devoluciones dobles se triagen primero",
            evidencias_run_ids=[run])
        ref = prop.referencia
        ids_hitl.append(prop.propuesta_id)
        assert prop.estado == "pendiente" and not prop.publicado
        hitl.aprobar(prop.propuesta_id, "steward:ana",
                     reanudar=memoria.reanudar)
        with bd.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM banco.memoria"
                        " WHERE clave = %s", (ref,))
            assert cur.fetchone()["n"] == 1     # publicada

        # 3. Una decisión del runtime del 37.2 que encola con el
        #    ctx["sujeto"] (clase incluida) y pausa en interrupt().
        rt.autorizar = lambda d: "require_human"

        def _pausa(payload):
            raise _Pausa()

        rt.interrupt = _pausa
        ctx = {"sujeto": con_clase,
               "humano": {"id": f"E-{suf}", "auth": "strong"},
               "run": uuid.uuid4().hex, "proposito": "soporte",
               "entorno": "dev", "hilo": hilo_rt,
               "agente": {"id": "banco.sepa.backoffice",
                          "version": "1.0.0"}}
        llamada = {"name": "marcar_resuelta", "id": "t1",
                   "args": {"referencia": f"REF-{suf}",
                            "motivo": "duplicada"}}
        with pytest.raises(_Pausa):
            rt.decidir(ctx, llamada)
        with bd.cursor() as cur:
            cur.execute("SELECT id, estado, sujeto FROM"
                        " banco.aprobaciones WHERE hilo = %s",
                        (hilo_rt,))
            fila = cur.fetchone()
        ids_hitl.append(fila["id"])
        assert fila["estado"] == "pendiente"
        # La columna habla UNA grafía: el id a secas (35.6).
        assert fila["sujeto"] == sujeto

        # 4. El sujeto ejerce su derecho. El expediente entra con
        #    la grafía del runtime, la contraria a la de la tool.
        r = suprimir_sujeto(con_clase, exp, "dpo:test")
        assert r.sujeto == sujeto
        assert len(r.almacenes) == 7        # el receipt cuenta todo
        assert r.completo is False
        assert r.pendientes == ["4 trazas"]  # delegado, con dueño
        auditoria = r.almacenes[4]
        assert auditoria.accion == "redactado"
        assert auditoria.filas == 1          # la fila del runtime
        with bd.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM"
                        " banco.supresiones WHERE solicitud = %s",
                        (exp,))
            assert cur.fetchone()["n"] == 7  # una fila por almacén

        # 5. NINGÚN almacén del sujeto queda vivo, en ninguna de
        #    las dos grafías; la colectiva (de nadie) sobrevive.
        with bd.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM banco.memoria"
                        " WHERE sujeto IN (%s, %s)",
                        (sujeto, con_clase))
            assert cur.fetchone()["n"] == 0
            cur.execute("SELECT count(*) AS n FROM store WHERE"
                        " prefix LIKE %s",
                        (f"banco.%.{sujeto}",))
            assert cur.fetchone()["n"] == 0
            cur.execute("SELECT estado, aprobador, propuesta,"
                        " purgado_en FROM banco.aprobaciones"
                        " WHERE id = %s", (fila["id"],))
            f = cur.fetchone()
            cur.execute("SELECT count(*) AS n FROM banco.memoria"
                        " WHERE clave = %s", (ref,))
            assert cur.fetchone()["n"] == 1  # la FAQ no es de nadie
        assert f["estado"] == "rechazada"    # cerrada, no rota
        assert f["aprobador"] == "sistema:supresion"
        assert f["propuesta"] == {} and f["purgado_en"] is not None
        assert fila["id"] not in [p["id"] for p in hitl.pendientes()]

        # 6. La reejecución del decidir enruta el cierre desde la
        #    fila firmada, sin volver a pausar (37.2).
        veredicto = rt.decidir(ctx, llamada)
        assert veredicto == "RECHAZADO: sujeto en supresión (34.6)"

        # 7. Y el hecho queda en el registro del 16.6, por sujeto.
        with bd.cursor() as cur:
            cur.execute("SELECT count(*) AS n FROM banco.registro_ia"
                        " WHERE sujeto = %s AND tipo ="
                        " 'rgpd_supresion'", (sujeto,))
            assert cur.fetchone()["n"] == 1
    finally:
        memoria.CTX = ctx_viejo
        rt.autorizar, rt.interrupt = aut_viejo, int_viejo
        with bd, bd.cursor() as cur:
            if ids_hitl:
                cur.execute("DELETE FROM banco.aprobaciones WHERE"
                            " id = ANY(%s)", (ids_hitl,))
            if ref is not None:
                cur.execute("DELETE FROM banco.memoria WHERE"
                            " clave = %s", (ref,))
            cur.execute("DELETE FROM banco.memoria WHERE"
                        " sujeto IN (%s, %s)", (sujeto, con_clase))
            cur.execute("DELETE FROM banco.supresiones WHERE"
                        " solicitud = %s", (exp,))
            cur.execute("DELETE FROM banco.registro_ia WHERE"
                        " sujeto = %s", (sujeto,))
            cur.execute("DELETE FROM store WHERE prefix LIKE %s",
                        (f"banco.%.{sujeto}",))
            if store_creada:
                cur.execute("DROP TABLE store")
