IBAN_CLIENTE = "ES9121000418450200051332"

# El «core bancario» de este capítulo: un dict. En el M11 será
# Postgres, y el loop no cambiará ni una línea.
AHORA = datetime.now()


def hace(**delta) -> str:
    """La semilla cuelga del reloj: con la fecha escrita en duro
    caduca sola y historial_cuenta se queda sin movimientos."""
    return (AHORA - timedelta(**delta)).isoformat(timespec="seconds")


TRANSFERENCIAS = {
    "REF-4471": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler mensual",
                 "fecha": hace(hours=3, seconds=19)},
    "REF-4472": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler mensual",
                 # La gemela, 19 segundos después: ese hueco es
                 # todo lo que distingue un doble envío.
                 "fecha": hace(hours=3)},
    "REF-4468": {"iban": IBAN_CLIENTE, "importe_cent": 4990,
                 "beneficiario": "ES4814650100722030876293",
                 "concepto": "Cuota gimnasio",
                 "fecha": hace(days=1)},
}
CASOS: dict = {}          # el único efecto lateral del agente


def eur(cent: int) -> str:
    """Decisión 6: formatear dinero es código, nunca una llamada."""
    signo, cent = ("-" if cent < 0 else ""), abs(cent)
    return f"{signo}{cent // 100},{cent % 100:02d} EUR"
