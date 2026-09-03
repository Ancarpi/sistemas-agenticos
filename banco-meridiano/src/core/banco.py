IBAN_CLIENTE = "ES9121000418450200051332"

# El «core bancario» de este capítulo: un dict. En el M11 será
# Postgres, y el loop no cambiará ni una línea.
TRANSFERENCIAS = {
    "REF-4471": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler septiembre",
                 "fecha": "2026-09-01T09:14:22"},
    "REF-4472": {"iban": IBAN_CLIENTE, "importe_cent": 128450,
                 "beneficiario": "ES6000491500051234567892",
                 "concepto": "Alquiler septiembre",
                 "fecha": "2026-09-01T09:14:41"},
    "REF-4468": {"iban": IBAN_CLIENTE, "importe_cent": 4990,
                 "beneficiario": "ES4814650100722030876293",
                 "concepto": "Cuota gimnasio",
                 "fecha": "2026-08-31T20:02:10"},
}
CASOS: dict = {}          # el único efecto lateral del agente


def eur(cent: int) -> str:
    """Decisión 6: formatear dinero es código, nunca una llamada."""
    signo, cent = ("-" if cent < 0 else ""), abs(cent)
    return f"{signo}{cent // 100},{cent % 100:02d} EUR"
