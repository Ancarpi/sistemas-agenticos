# Contribuir

Este paquete acompaña a un libro, y eso fija qué se contribuye dónde. Dos carriles, y la distinción importa:

## Erratas del libro → issue, nunca PR

Si un bloque de código del manual no hace lo que la página dice, eso es una **errata** y su destino es `ERRATA.md`, que promete fechar cada corrección y decir qué versión de qué librería la provocó. Abre una issue con la plantilla **«Errata del libro»**: pide el apartado, qué hiciste, qué esperabas, qué salió y las versiones instaladas (`pip freeze | grep -E 'langchain|langgraph|mcp|livekit|psycopg'`). **Sin las versiones no se puede fechar la corrección**, así que la plantilla las exige --- no es burocracia, es el contrato del 0.4.

No mandes un PR que «arregle» código en `banco/`: ver la regla siguiente.

## Problemas del paquete → issue o PR

Bugs en `tools/`, mejoras en `skills/`, `agents/isa/`, `schemas/` o `knowledge/`: plantilla **«Problema del paquete»**, o directamente un PR.

### La regla que no se negocia: `banco/` no se edita

Ese árbol lo genera `tools/extraer_banco/` desde el libro, byte a byte. Cualquier edición ahí la pisa la siguiente extracción sin dejar rastro. Si algo está mal en `banco/`, el arreglo es una errata (carril de arriba) que acaba corrigiendo el libro, y el árbol se re-extrae. Los únicos ficheros de ese directorio que no genera el extractor son `README.md`, `pyproject.toml`, `conftest.py` y `docker-compose.yml` --- y aun así van con el autor, porque hablan con la voz del libro --- más dos artefactos del libro traducidos a datos a mano, `contratos/triage_sepa.contract.yaml` y `evals/capstone_gate.eval.yaml`, que siguen la misma regla: si están mal, el carril es la errata. `.env.example` tampoco lo genera el extractor, y tampoco se edita: lo escribe `tools/generar_env/generar_env.py` desde el bloque `.env` del 0.4.

### Reglas del resto del árbol

- **`knowledge/`: una regla, un fichero, una fila en `INDEX.md`.** Las skills citan reglas **por ruta** en su sección `## Canon`, nunca las copian. Si tocas los `owners` de un fichero de conocimiento, la bidireccionalidad se mantiene: la skill que figura ahí lo cita, y viceversa.
- **Nombrado:** todo artefacto lleva prefijo `isa-`. La única excepción es la de las lentes en `agents/isa/`, documentada en el README.
- **Mensajes del validador:** en español y en ASCII, una línea por defecto con la forma `ruta/dentro/del/artefacto: qué falta`. Un defecto que solo dice «inválido» no se acepta.
- **`tools/`: solo stdlib.** Los dos scripts corren en un contenedor pelado con `python3` y nada más; una dependencia nueva ahí es un cambio de contrato, no un detalle.
- **Nada de prosa del libro.** La licencia MIT cubre el código; la prosa sigue siendo del autor. Un PR que pegue párrafos del manual no se puede aceptar, tenga la intención que tenga.

### Antes de abrir el PR

El CI (`.github/workflows/promesas.yml`) comprueba promesas concretas del README, y todas corren en local sin montar nada --- la única que quiere un Postgres, `esquemas.py`, salta limpio y lo dice si no le das `ESQUEMAS_URL`:

```bash
python3 -m compileall -q .                                  # todo .py compila
python3 tools/isa_validate/isa_validate.py context-contract banco/contratos/triage_sepa.contract.yaml
python3 tools/isa_validate/isa_validate.py capability       banco/tools/bloquear_tarjeta.capability.yaml
python3 tools/isa_validate/isa_validate.py eval-card        banco/evals/capstone_gate.eval.yaml
python3 tools/isa_validate/isa_validate.py agent-package    banco/catalogo/cards-disputes/agent.yaml
python3 tools/isa_validate/isa_validate.py capability tools/isa_validate/casos-negativos/capability-sin-idempotencia.yaml  # debe salir con 1
python3 tools/isa_validate/isa_validate.py eval-card  tools/isa_validate/casos-negativos/eval-card-sin-n-cases.yaml        # debe salir con 1
python3 tools/extraer_banco/guiones.py                      # todo bloque __main__ es la ultima sentencia de su guion
ESQUEMAS_URL=postgresql://...  python3 tools/extraer_banco/esquemas.py   # los .sql aplican en su orden (salta sin la variable)
```

Si tu cambio añade una palabra clave de JSON Schema a un esquema, el validador tiene que aprenderla en el mismo PR: un esquema con reglas que nadie comprueba es exactamente lo que este paquete existe para impedir (`tools/isa_validate/API.md`).
