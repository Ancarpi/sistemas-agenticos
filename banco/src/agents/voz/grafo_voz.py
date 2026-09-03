# grafo_voz.py --- el cerebro de la llamada. Dos herramientas y
# ninguna más: en voz, cada herramienta de más es un turno de más.
import os

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolCallLimitMiddleware, wrap_tool_call,
)
