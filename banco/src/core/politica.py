# src/core/politica.py --- el motor de política de la plataforma.
# Entra el dict de seis claves del 35.2 y sale una de las cinco
# cadenas. Las reglas no están aquí: están en el bundle del 26.2,
# que se revisa, se despliega y se revierte sin tocar este fichero.
import logging
import os

import yaml

BUNDLE = os.environ.get("POLITICA_BUNDLE", "config/politica.yaml")
log = logging.getLogger("politica")

# Las seis claves del 35.2. Si falta una no hay situación que
# evaluar, y lo que no se evalúa no se autoriza.
CLAVES = ("subject", "agent", "tool", "resource", "context", "risk")
# De la más permisiva a la más estricta. Las dos guardas de abajo
# solo mueven la decisión hacia la derecha de esta tupla: pueden
# cerrar de más, nunca abrir de menos.
ORDEN = ("allow", "require_dry_run", "require_step_up_auth",
         "require_human", "deny")
PELDANOS = ("L0", "L1", "L2", "L3", "L4")          # el Anexo H
_VISTO = {"mtime": None, "datos": None}


def _bundle() -> dict | None:
    """Relee por `mtime` en cada llamada, como el registro del
    32.3. Viaja en el ConfigMap del 27.2, donde el kubelet publica
    moviendo `..data`: un `inotify` se queda ciego y un `stat` no."""
    try:
        mtime = os.stat(BUNDLE).st_mtime_ns
        if mtime != _VISTO["mtime"]:
            with open(BUNDLE, encoding="utf-8") as f:
                _VISTO.update(mtime=mtime, datos=yaml.safe_load(f))
    except (OSError, yaml.YAMLError):
        # Un fichero a medio escribir no releva al último bueno,
        # igual que el catálogo del 33.6. En frío no hay último
        # bueno y se deniega todo.
        log.exception("politica: bundle ilegible")
    return _VISTO["datos"]


def _valor(peticion: dict, ruta: str):
    """`resource.data_class` sobre el dict del 35.2."""
    dato = peticion
    for parte in ruta.split("."):
        dato = dato.get(parte) if isinstance(dato, dict) else None
    return dato


def _casa(cuando: dict, peticion: dict) -> bool:
    """Una lista es un OR y un escalar es esa lista de uno. La
    regla que pide un atributo que no llegó, no casa."""
    for ruta, esperado in cuando.items():
        valor = _valor(peticion, ruta)
        if not isinstance(esperado, list):
            esperado = [esperado]
        if valor is None or valor not in esperado:
            return False
    return True


def _regla(bundle: dict, peticion: dict) -> str:
    """La primera que case, con el `por_defecto` de última regla y
    su `id` al log: una denegación que no dice quién la tomó no se
    audita ni se revierte. Una decisión inventada revienta aquí."""
    resto = {"id": "por-defecto", "cuando": {},
             "entonces": bundle["por_defecto"]}
    for regla in list(bundle["reglas"]) + [resto]:
        if _casa(regla["cuando"], peticion):
            log.info("politica %s: %s -> %s", bundle["version"],
                     regla["id"], regla["entonces"])
            if regla["entonces"] not in ORDEN:
                raise ValueError(regla["id"])
            return regla["entonces"]


def _limite_economico(bundle: dict, peticion: dict, d: str) -> str:
    """La regla que más se olvida. Si la herramienta mueve dinero y
    la petición no declara cuánto, se deniega."""
    limites = bundle["limites"]
    if _valor(peticion, "tool.id") not in limites["mueve_dinero"]:
        return d
    importe = _valor(peticion, "resource.amount_eur")
    if not isinstance(importe, (int, float)):
        return "deny"
    if importe > limites["importe_autonomo_eur"]:
        return max(d, "require_human", key=ORDEN.index)
    return d


def _paso_reforzado(bundle: dict, peticion: dict, d: str) -> str:
    """Del peldaño que diga el bundle hacia arriba, un sujeto
    HUMANO autenticado de forma débil sube a step-up (Anexo H). Al
    sujeto de carga del 35.3 no hay a quién pedirle un segundo
    factor, y lo que puede hacer se lo acota su regla del bundle,
    que no llega a L4. La guarda sigue cerrada por defecto: un
    `subject.kind` que no llegue cuenta como humano."""
    if _valor(peticion, "subject.kind") == "workload":
        return d
    desde = PELDANOS.index(bundle["limites"]["step_up_desde"])
    nivel = PELDANOS.index(_valor(peticion, "risk.autonomy_level"))
    debil = _valor(peticion, "subject.auth_level") != "strong"
    if nivel >= desde and debil:
        return max(d, "require_step_up_auth", key=ORDEN.index)
    return d


def autorizar(peticion: dict) -> str:
    """La única función que el resto del libro importa. El
    `runtime.py` del 37.2 la llama una vez por herramienta y
    escribe lo que devuelve en el `policy.decision` del 36.1."""
    try:
        bundle = _bundle()
        if bundle is None or any(k not in peticion for k in CLAVES):
            log.error("politica: sin bundle o petición incompleta")
            return "deny"
        decision = _regla(bundle, peticion)
        decision = _limite_economico(bundle, peticion, decision)
        return _paso_reforzado(bundle, peticion, decision)
    except Exception:
        # Un peldaño inventado, un tipo raro en el YAML o una
        # clave que falta acaban aquí, y acabar aquí es denegar. El
        # `exception` separa el deny que decidió la política del
        # que decidió un fallo.
        log.exception("politica: evaluación fallida")
        return "deny"


# --- costura PENDIENTE del M35.2 (extraer_banco) ---
# PENDIENTE. La forma de la llamada del 35.2 y las cinco decisiones del engine: es una llamada de ejemplo a nivel de modulo, asi que hay que comentarla o moverla a un test o el import revienta.
# El script no la aplica en su sitio: eso es una decision. Ver COSTURAS.md.
decision = policy_engine.authorize({
  'subject': {'user_id': 'C-99', 'auth_level': 'strong'},
  'agent': {'id': 'banco.chat.support.v4', 'version': '4.2.1'},
  'tool': {'id': 'core.accounts.read_movements', 'kind': 'read'},
  'resource': {'account_owner': 'C-99', 'data_class': 'confidential'},
  'context': {'purpose': 'customer_support', 'env': 'prod'},
  'risk': {'autonomy_level': 'L0'}
})
# allow | deny | require_human | require_dry_run | require_step_up_auth
