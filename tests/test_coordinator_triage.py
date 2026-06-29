"""
Testes para triage e SRP do Coordinator.

Cenarios:
  1. Classificacao correta com word boundaries
  2. _route_simple nao depende de WriterAgent
  3. _circuit_breaker_fallback retorna success=False
  4. Edge cases: string vazia, textos longos sem keywords
"""

import os
import sys
from unittest.mock import AsyncMock, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.coordinator import Coordinator
from core.llm_manager import Request


class TestCoordinatorTriage:
    """Testes para a classificacao de requisicoes."""

    def make_coordinator(self):
        c = Coordinator.__new__(Coordinator)
        c.llm = Mock()
        c.memory = Mock()
        c.researcher = Mock()
        c.analyst = Mock()
        c.writer = Mock()
        return c

    def test_simple_cases(self):
        c = self.make_coordinator()
        cases = [
            "Qual e a capital do Brasil?",
            "O que e Python?",
            "Me explique o que e IA",
            "O preco do cafe hoje",
            "",
        ]
        for text in cases:
            assert c._classify(text) == "simple", f"Esperado 'simple' para '{text}'"

    def test_dados_validados_is_simple(self):
        """'dados validados' nao deve conter '\\bdados\\b' porque e substring de 'validados'"""
        c = self.make_coordinator()
        result = c._classify("dados validados")
        assert result == "simple", (
            f"'dados validados' classificado como '{result}', "
            f"mas 'dados' nao e palavra independente em 'validados'"
        )

    def test_complex_cases(self):
        c = self.make_coordinator()
        cases = [
            ("Pesquise sobre inteligencia artificial", "complex"),
            ("Faca uma analise dos dados", "complex"),
            ("Escreva um relatorio sobre o projeto", "complex"),
            ("Compare as duas abordagens propostas", "complex"),
            ("Preciso de um levantamento estrategico", "complex"),
            ("Pesquisador e uma profissao interessante", "complex"),
            ("Buscar informacoes sobre cambio", "complex"),
            ("Quero um relatorio completo", "complex"),
            ("Preciso de dados e comparar tendencias", "complex"),
        ]
        for text, expected in cases:
            result = c._classify(text)
            assert result == expected, (
                f"Esperado '{expected}' para '{text}', obtido '{result}'"
            )

    def test_weak_matches_require_two(self):
        """Palavras fracas exigem 2+ matches para classificar como complex."""
        c = self.make_coordinator()
        single_weak = [
            "Preciso de dados atualizados",
            "Pode resumir isso?",
            "Sugerir uma abordagem",
        ]
        for text in single_weak:
            assert c._classify(text) == "simple", (
                f"Apenas 1 match fraco para '{text}' deveria ser 'simple'"
            )

    def test_weak_matches_two_triggers_complex(self):
        c = self.make_coordinator()
        cases = [
            "Preciso de dados para comparar duas opcoes",
            "Analise os dados e resuma os resultados",
            "Sugerir melhorias baseadas em tendencias recentes",
        ]
        for text in cases:
            assert c._classify(text) == "complex", (
                f"2+ matches fracos para '{text}' deveria ser 'complex'"
            )

    def test_long_text_without_keywords_is_simple(self):
        """Texto longo (>15 palavras) sem keywords ainda e simple."""
        c = self.make_coordinator()
        text = "Qual e o significado da vida do universo e todas as coisas"
        assert c._classify(text) == "simple"

    def test_route_simple_no_writer_agent(self):
        """_route_simple NAO deve usar WriterAgent."""
        c = self.make_coordinator()

        async def run():
            request = Request(prompt="Responda de forma clara e direta em portugues:\nteste",
                            max_tokens=500, temperature=0.7)
            c.llm.generate = AsyncMock(return_value="resposta direta")
            c.writer = None

            result = await c._route_simple("teste")

            assert result["success"] is True
            assert result["final_response"] == "resposta direta"
            c.llm.generate.assert_awaited_once()

        import asyncio
        asyncio.run(run())

    def test_circuit_breaker_returns_success_false(self):
        c = self.make_coordinator()

        async def run():
            c.llm.generate = AsyncMock(return_value="fallback explicativo")
            result = await c._circuit_breaker_fallback("teste")

            assert result["success"] is False, "Circuit breaker deve retornar success=False"
            assert result["circuit_breaker"] is True
            assert "fontes externas" in result["error"]


        import asyncio
        asyncio.run(run())

    def test_circuit_breaker_no_writer_agent(self):
        """_circuit_breaker_fallback NAO deve usar WriterAgent."""
        c = self.make_coordinator()

        async def run():
            c.llm.generate = AsyncMock(return_value="resposta de fallback")
            c.writer = None

            result = await c._circuit_breaker_fallback("teste")

            assert result["success"] is False
            c.llm.generate.assert_awaited_once()

        import asyncio
        asyncio.run(run())


if __name__ == "__main__":
    import traceback
    t = TestCoordinatorTriage()
    passed = 0
    failed = 0
    for name in dir(t):
        if name.startswith("test_"):
            try:
                getattr(t, name)()
                print(f"  [PASS] {name}")
                passed += 1
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")
                traceback.print_exc()
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
