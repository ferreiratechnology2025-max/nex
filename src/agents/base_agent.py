"""Agente base para orquestracao"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    COORDINATOR = "coordinator"


@dataclass
class AgentTask:
    id: str
    description: str
    assigned_to: AgentRole
    status: str = "pending"
    result: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class BaseAgent(ABC):
    """Classe base para todos os agentes especializados"""

    def __init__(self, role: AgentRole, llm_manager, memory_manager=None):
        self.role = role
        self.llm = llm_manager
        self.memory = memory_manager
        logger.info(f"Agente {role.value} inicializado")

    @abstractmethod
    async def execute(self, task: AgentTask, context: Dict) -> Dict:
        pass

    async def _generate(self, prompt: str, system_prompt: str = None) -> str:
        from src.core.llm_manager import Request
        try:
            return await asyncio.wait_for(
                self.llm.generate(Request(prompt=prompt), system_prompt=system_prompt),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout gerando em {self.role.value}: {prompt[:50]}...")
            return "Erro: tempo limite excedido na geracao"

    async def _generate_safe(self, prompt: str, system_prompt: str = None) -> str:
        """Gera resposta com fallback local explicito em caso de falha do backend remoto (429, timeout, etc).

        O LLMManager.generate() ja possui cascata interna (OpenRouter → llama_cpp → HuggingFace).
        Esta camada extra garante que, mesmo que a cascata complete retorne mensagem de erro,
        o agente tente forcar o uso do HuggingFace local antes de desistir.
        """
        from src.core.llm_manager import Request, BackendType
        result = await self._generate(prompt, system_prompt)

        if "todos os backends" in result.lower() or "indispon" in result.lower():
            logger.warning(f"{self.role.value}: backend remoto falhou, forcando fallback local")
            try:
                self.llm.backend = BackendType.HUGGINGFACE
                if not self.llm.is_huggingface_ready():
                    await asyncio.get_running_loop().run_in_executor(None, self.llm._init_huggingface)
                if self.llm.is_huggingface_ready():
                    result = await asyncio.wait_for(
                        self.llm._generate_huggingface(Request(prompt=prompt)),
                        timeout=120.0
                    )
            except Exception as e2:
                logger.error(f"{self.role.value}: fallback local tambem falhou: {e2}")

        return result

    async def _log_execution(self, task: AgentTask, result: Dict):
        logger.info(f"Agente {self.role.value} completou tarefa {task.id}: {task.description[:50]}")
        if self.memory:
            await self.memory.salvar_memoria(
                f"[AGENT:{self.role.value}] Tarefa: {task.description}\nResultado: {str(result)[:500]}",
                importancia=0.8,
            )
