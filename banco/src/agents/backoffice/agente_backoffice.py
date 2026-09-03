# agente_backoffice.py --- el nano_agent del 3.3, industrializado.
from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware, ModelCallLimitMiddleware,
    ModelRetryMiddleware, PIIMiddleware, SummarizationMiddleware,
)
