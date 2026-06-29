"""Coordenador - orquestracao em DAG com streaming SSE, circuit breaker e fallback"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, AsyncGenerator

from .base_agent import AgentTask, AgentRole
from .researcher_agent import ResearcherAgent
from .analyst_agent import AnalystAgent
from .writer_agent import WriterAgent

logger = logging.getLogger(__name__)


class Coordinator:
    """Orquestrador DAG com streaming de estado e circuit breaker.

    Fluxo:
      Triage -> (simple: resposta direta | complex: Plan -> Research -> Analyze -> Write)

    Circuit breaker:
      Se Research retornar vazio (0 resultados), o pipeline e abortado e o sistema
      gera uma resposta degradada usando fallback local, impedindo alucinacao.

    Streaming:
      execute_stream() e um async generator que produz events {"stage", "status", "detail"}
      para alimentar Server-Sent Events (SSE) na API.
    """

    # Padroes fortes (re.search com \b): 1 ocorrencia ja classifica como complex
    _STRONG_PATTERNS = [
        r'\bpesquis\w*',
        r'\bbuscar\b', r'\bbusca\b',
        r'\bweb\b', r'\binternet\b', r'\bonline\b',
        r'\bdocumento\b', r'\barquivo\b',
        r'\brelatorio\b', r'\breport\b',
        r'\bcontrato\b', r'\bplanilha\b',
        r'\bnoticia\b', r'\bnotícia\b',
        r'\brecente\b', r'\batualizado\b',
        r'\bgithub\b', r'\brepositorio\b', r'\brepositório\b',
        r'\bcódigo\b', r'\bcodigo\b',
        r'\bcompar\w*',
        r'\blevantamento\b',
        r'\bestrat\w*',
        r'\bplanej\w*',
        r'\bavali\w*',
    ]

    # Padroes fracos: exigem 2+ ocorrencias para classificar como complex
    _WEAK_PATTERNS = [
        r'\banalis\w*', r'\banalise\b', r'\banálise\b',
        r'\btendencias\b', r'\btendências\b',
        r'\bdados\b',
        r'\bresumir\b', r'\bsumario\b', r'\bsumário\b',
        r'\bsugerir\b', r'\brecomendar\b',
    ]

    # Frases inteiras que disparam rota complex
    _PHRASE_TRIGGERS = (
        "no arquivo", "no documento",
        "nos arquivos", "nos documentos",
        "me mostre",
    )

    def __init__(self, llm_manager, memory_manager, web_search_processor=None, document_manager=None):
        self.llm = llm_manager
        self.memory = memory_manager

        self.researcher = ResearcherAgent(llm_manager, memory_manager, web_search_processor, document_manager)
        self.analyst = AnalystAgent(llm_manager, memory_manager)
        self.writer = WriterAgent(llm_manager, memory_manager)

        logger.info("Coordenador DAG inicializado")

    # ------------------------------------------------------------------ #
    # Public API - Streaming (SSE)
    # ------------------------------------------------------------------ #

    async def execute_stream(self, objective: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Async generator que produz eventos de status + resultado final.

        Uso:
            async for event in coordinator.execute_stream("pergunta"):
                # event: {"stage": "...", "status": "...", "detail": "..."}
                # event final: {"stage": "complete", "status": "done", "result": {...}}
        """
        complexity = self._classify(objective)
        yield self._event("triage", "complete", f"Classificado como: {complexity}")

        if complexity == "simple":
            result = await self._route_simple(objective)
            yield self._event("complete", "done", "", result=result)
            return

        # ---- Complex path ----
        yield self._event("plan", "running", "Criando plano de execucao...")
        plan = await self._plan(objective)
        yield self._event("plan", "complete", f"Plano: {len(plan)} passos")

        # Research
        yield self._event("research", "running", "Pesquisando web e documentos...")
        research_task = AgentTask(
            id="research", description=objective, assigned_to=AgentRole.RESEARCHER,
        )
        research_results = await self._safe_execute(
            self.researcher.execute(research_task, {"plan": plan}),
            default={"web_results": [], "document_results": [], "summary": ""},
            step_name="Research",
        )

        had_data = bool(research_results.get("web_results") or research_results.get("document_results"))
        had_error = "error" in research_results

        if not had_data or had_error:
            yield self._event("research", "failed",
                "Pesquisa nao retornou dados uteis" if not had_data
                else f"Erro na pesquisa: {research_results.get('error')}")

            yield self._event("circuit_breaker", "active",
                "Fontes externas indisponiveis - gerando resposta com fallback local")
            result = await self._circuit_breaker_fallback(objective)
            yield self._event("complete", "done", "", result=result)
            return

        yield self._event("research", "complete", "Pesquisa concluida")

        # Analysis
        yield self._event("analysis", "running", "Analisando dados obtidos...")
        analysis_task = AgentTask(
            id="analysis", description=objective, assigned_to=AgentRole.ANALYST,
        )
        analysis_results = await self._safe_execute(
            self.analyst.execute(analysis_task, {"research_results": research_results}),
            default={"key_findings": [], "patterns": [], "recommendations": [], "summary": ""},
            step_name="Analysis",
        )
        yield self._event("analysis", "complete", "Analise concluida")

        # Write
        yield self._event("write", "running", "Gerando resposta final...")
        write_task = AgentTask(
            id="write", description=objective, assigned_to=AgentRole.WRITER,
        )
        writer_output = await self._safe_execute(
            self.writer.execute(write_task, {
                "analysis_results": analysis_results,
                "objective": objective,
            }),
            default={"final_response": "Erro ao gerar resposta final.", "format": "report", "sections": []},
            step_name="Writer",
        )
        yield self._event("write", "complete", "Resposta gerada")

        if self.memory:
            await self._save_to_memory(
                f"[ORCHESTRATED] {objective}\nResultado: {str(writer_output.get('final_response', ''))[:500]}",
                1.2,
            )

        result = {
            "success": True,
            "objective": objective,
            "plan": plan,
            "research_summary": research_results.get("summary", ""),
            "analysis": analysis_results.get("summary", ""),
            "final_response": writer_output.get("final_response", ""),
            "error": "",
        }
        yield self._event("complete", "done", "", result=result)

    # ------------------------------------------------------------------ #
    # Public API - Blocking (compatibilidade)
    # ------------------------------------------------------------------ #

    async def execute(self, objective: str) -> Dict[str, Any]:
        """Versao blocking (agrega o stream e retorna o resultado final)."""
        result = {"success": False, "error": "Sem resposta", "final_response": ""}
        async for event in self.execute_stream(objective):
            if event.get("stage") == "complete" and event.get("status") == "done":
                result = event.get("result", result)
        return result

    # ------------------------------------------------------------------ #
    # Triage
    # ------------------------------------------------------------------ #

    def _classify(self, objective: str) -> str:
        """Classifies a request as simple or complex using word boundaries.

        Uses re.search with \\b to avoid false positives:
        - "dados validados" -> "dados" does not match "validados" -> simple
        - "pesquisa de mercado" -> "\\bpesquis\\w*" matches "pesquisa" -> complex
        """
        if not objective:
            return "simple"

        text_lower = objective.lower()
        words = text_lower.split()

        for pattern in self._STRONG_PATTERNS:
            if re.search(pattern, text_lower):
                return "complex"

        for phrase in self._PHRASE_TRIGGERS:
            if phrase in text_lower:
                return "complex"

        weak_matches = sum(1 for pattern in self._WEAK_PATTERNS if re.search(pattern, text_lower))
        if weak_matches >= 2:
            return "complex"

        if len(words) > 15:
            return "complex"

        return "simple"

    # ------------------------------------------------------------------ #
    # Rotas
    # ------------------------------------------------------------------ #

    async def _route_simple(self, objective: str) -> Dict[str, Any]:
        logger.info("Simple route: direct response")
        from core.llm_manager import Request

        prompt = f"Responda de forma clara e direta em portugues:\n{objective}"
        request = Request(prompt=prompt, max_tokens=500, temperature=0.7)
        response = await self.llm.generate(request)

        if self.memory:
            await self._save_to_memory(f"[SIMPLE] {objective}\nResposta: {response[:300]}", 0.7)

        return {
            "success": True,
            "objective": objective,
            "plan": ["1. Responder diretamente"],
            "research_summary": "",
            "analysis": "",
            "final_response": response,
            "error": "",
        }

    async def _circuit_breaker_fallback(self, objective: str) -> Dict[str, Any]:
        """Degraded response when circuit breaker opens (external search failed).

        Returns success=False to indicate the operation was not completed
        successfully, rather than masking the failure.
        """
        logger.warning("Circuit breaker ativo: resposta com fallback local")
        from core.llm_manager import Request

        prompt = (
            f"O usuario perguntou: {objective}\n\n"
            "Nao foi possivel acessar fontes externas (web ou documentos) para responder. "
            "Explique de forma educada que a pesquisa externa esta temporariamente "
            "indisponivel e ofereca ajuda com base no conhecimento existente."
        )
        request = Request(prompt=prompt, max_tokens=300, temperature=0.7)
        response = await self.llm.generate(request)

        return {
            "success": False,
            "objective": objective,
            "plan": ["1. Tentar pesquisa", "2. Falha em fontes externas (circuit breaker)"],
            "research_summary": "Pesquisa indisponivel - circuit breaker ativado",
            "analysis": "",
            "final_response": response,
            "error": "circuit_breaker: fontes externas indisponiveis",
            "circuit_breaker": True,
        }

    # ------------------------------------------------------------------ #
    # Plan
    # ------------------------------------------------------------------ #

    async def _plan(self, objective: str) -> List[str]:
        prompt = f"""
Objetivo: {objective}
Crie um plano de execucao com estes agentes:
1. Researcher - Pesquisa na web e documentos
2. Analyst - Analisa dados e extrai insights
3. Writer - Gera resposta final
Retorne passos numerados:"""
        text = await self.writer._generate_safe(prompt)
        plan = [p.strip() for p in text.split("\n") if p.strip() and p.strip()[0].isdigit()]
        plan = plan if plan else ["1. Pesquisar", "2. Analisar", "3. Escrever"]

        if self.memory:
            await self._save_to_memory(f"[PLAN] {objective}\n" + "\n".join(plan), 0.9)
        return plan

    # ------------------------------------------------------------------ #
    # Utilitarios
    # ------------------------------------------------------------------ #

    async def _safe_execute(self, coro, default: Dict, step_name: str) -> Dict:
        try:
            return await asyncio.wait_for(coro, timeout=60.0)
        except asyncio.TimeoutError:
            logger.error(f"{step_name}: timeout apos 60s")
            return {**default, "error": f"{step_name}: timeout"}
        except Exception as e:
            logger.error(f"{step_name}: erro: {e}")
            return {**default, "error": f"{step_name}: {str(e)}"}

    async def _save_to_memory(self, text: str, importancia: float = 1.0):
        try:
            await asyncio.wait_for(
                self.memory.salvar_memoria(text, importancia=importancia),
                timeout=5.0,
            )
        except Exception:
            pass

    @staticmethod
    def _event(stage: str, status: str, detail: str = "", result: Dict = None) -> Dict:
        event = {"stage": stage, "status": status, "detail": detail}
        if result is not None:
            event["result"] = result
        return event
