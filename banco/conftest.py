# conftest.py --- la mitad de lo que `uv run pytest tests/` necesita y
# que el arbol del Ejercicio 0.1 no da solo. La otra mitad es el
# `pythonpath` de [tool.pytest.ini_options] en pyproject.toml, que pone
# la raiz y `src/core` en el sys.path porque el libro escribe los
# ficheros planos y los importa planos: `from cumplimiento import
# AVISOS` (16.7).
#
# Aqui va el .env, que pytest no lee solo. Y hace falta antes de la
# primera assert, no dentro de ella: `src/core/cumplimiento.py` abre su
# pool en la linea 10, a nivel de modulo, asi que sin DATABASE_URL el
# import de tests/test_art50.py revienta, pytest aborta la tanda entera
# y ejecuta cero tests. Con el .env puesto y sin Postgres arriba, la
# tanda corre y test_registro.py falla, que es lo correcto: un test de
# RLS sin base de datos no mide nada y no tiene que saltarse.
import os
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent
ENV = RAIZ / ".env"
AVISOS: list[str] = []


def pytest_configure(config):
    if ENV.is_file():
        try:
            from dotenv import load_dotenv
        except ImportError:
            AVISOS.append("python-dotenv no esta instalado: uv sync")
        else:
            load_dotenv(ENV)
    else:
        AVISOS.append(f"no hay {ENV.name} (cp .env.example .env)")
    if not os.environ.get("DATABASE_URL"):
        AVISOS.append("sin DATABASE_URL no importa cumplimiento.py "
                      "(16.7) ni conecta test_registro.py")


def pytest_report_header(config):
    return [f"conftest: {a}" for a in AVISOS]
