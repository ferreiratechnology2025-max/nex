"""Agentes orquestrados para tarefas complexas"""

from .base_agent import BaseAgent, AgentRole, AgentTask
from .researcher_agent import ResearcherAgent
from .analyst_agent import AnalystAgent
from .writer_agent import WriterAgent
from .coordinator import Coordinator

__all__ = [
    "BaseAgent",
    "AgentRole",
    "AgentTask",
    "ResearcherAgent",
    "AnalystAgent",
    "WriterAgent",
    "Coordinator",
]
