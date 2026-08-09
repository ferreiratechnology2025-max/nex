"""Agente Analista - extrai insights e padroes"""

import logging
from typing import Dict, List
from .base_agent import BaseAgent, AgentRole, AgentTask

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Especialista em analise: extrai insights, padroes, recomendacoes"""

    def __init__(self, llm_manager, memory_manager=None):
        super().__init__(AgentRole.ANALYST, llm_manager, memory_manager)

    async def execute(self, task: AgentTask, context: Dict) -> Dict:
        logger.info(f"Analyst executando: {task.description}")
        data = context.get("research_results", {})

        analysis = {
            "key_findings": await self._extract_findings(data, task.description),
            "patterns": await self._identify_patterns(data),
            "recommendations": await self._generate_recommendations(data, task.description),
            "summary": "",
        }
        analysis["summary"] = await self._generate_summary(analysis)

        task.status = "completed"
        task.result = analysis
        return analysis

    async def _extract_findings(self, data: Dict, objective: str) -> List[str]:
        if not data:
            return ["Sem dados suficientes"]
        prompt = f"Objetivo: {objective}\nDados: {str(data)[:1500]}\nListe 3-5 principais achados:"
        text = await self._generate_safe(prompt)
        return [f.strip() for f in text.split("\n") if f.strip() and f.strip()[0] in ("-", "*", "•")] or [text[:200]]

    async def _identify_patterns(self, data: Dict) -> List[str]:
        if not data:
            return []
        prompt = f"Dados: {str(data)[:1000]}\nIdentifique padroes ou tendencias:"
        text = await self._generate_safe(prompt)
        return [p.strip() for p in text.split("\n") if p.strip()][:5]

    async def _generate_recommendations(self, data: Dict, objective: str) -> List[str]:
        prompt = f"Dados: {str(data)[:1000]}\nObjetivo: {objective}\nForneca 3-5 recomendacoes:"
        text = await self._generate_safe(prompt)
        return [r.strip() for r in text.split("\n") if r.strip()[:1].isdigit()] or [text[:200]]

    async def _generate_summary(self, analysis: Dict) -> str:
        prompt = f"""Resuma em 2-3 paragrafos:
Achados: {analysis.get('key_findings', [])}
Padroes: {analysis.get('patterns', [])}
Recomendacoes: {analysis.get('recommendations', [])}
Resumo:"""
        return await self._generate_safe(prompt)
