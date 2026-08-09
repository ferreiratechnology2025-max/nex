"""Agente Escritor - gera relatorios e respostas finais"""

import logging
from typing import Dict, Any
from .base_agent import BaseAgent, AgentRole, AgentTask

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Especialista em escrita: gera relatorios, respostas, documentacao"""

    def __init__(self, llm_manager, memory_manager=None):
        super().__init__(AgentRole.WRITER, llm_manager, memory_manager)

    async def execute(self, task: AgentTask, context: Dict) -> Dict:
        logger.info(f"Writer executando: {task.description}")
        analysis = context.get("analysis_results", {})
        objective = context.get("objective", task.description)

        output = {"final_response": "", "format": "report", "sections": []}

        task_lower = task.description.lower()
        if "email" in task_lower:
            output["format"] = "email"
        elif "resumo" in task_lower or "summary" in task_lower:
            output["format"] = "summary"
        elif "relatorio" in task_lower or "report" in task_lower:
            output["format"] = "report"

        output["final_response"] = await self._generate_final_output(objective, analysis, output["format"])
        if output["format"] == "report":
            output["sections"] = await self._generate_sections(analysis)

        task.status = "completed"
        task.result = output
        return output

    async def _generate_final_output(self, objective: str, analysis: Dict, fmt: str) -> str:
        prompt = f"""Objetivo: {objective}
Achados: {analysis.get('key_findings', [])}
Padroes: {analysis.get('patterns', [])}
Recomendacoes: {analysis.get('recommendations', [])}
Formato: {fmt}
Gere a resposta final em portugues, clara e profissional:"""
        return await self._generate_safe(prompt)

    async def _generate_sections(self, analysis: Dict) -> list:
        sections = []
        intro = await self._generate_safe(
            f"Escreva introducao para relatorio baseado em: {str(analysis.get('key_findings', [])[:200])}"
        )
        sections.append({"title": "Introducao", "content": intro})

        sections.append({
            "title": "Achados Principais",
            "content": "\n".join(f"- {f}" for f in analysis.get("key_findings", [])),
        })
        sections.append({
            "title": "Recomendacoes",
            "content": "\n".join(f"{i+1}. {r}" for i, r in enumerate(analysis.get("recommendations", []))),
        })

        conc = await self._generate_safe(
            f"Escreva conclusao para relatorio: {analysis.get('summary', '')[:200]}"
        )
        sections.append({"title": "Conclusao", "content": conc})
        return sections
