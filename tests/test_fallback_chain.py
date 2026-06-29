"""
Testes para fallback chain do LLM Manager.

Cenarios:
  1. Fallback chain order: OpenRouter fails -> llama_cpp succeeds
  2. All backends fail -> friendly error message
  3. Streaming fallback: OpenRouter fails -> llama_cpp stream succeeds
  4. Direct success (no fallback): OpenRouter succeeds immediately
"""

import os
import sys
import asyncio
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.llm_manager import LLMManager, Request


class TestFallbackChain:
    """Testes para a cadeia de fallback entre backends."""

    def make_manager(self):
        """Cria LLMManager com config minima e backends desabilitados."""
        m = LLMManager.__new__(LLMManager)
        m.config = {}
        m.memory_manager = None
        m.backend = None
        m._local_llm = None
        m._openrouter_client = None
        m._hf_ready = False
        m.hf_model = None
        m.hf_tokenizer = None
        m.last_backend_used = None
        m.last_fallback_triggered = False
        m.last_fallback_reason = None
        m.last_fallback_chain = "openrouter->llama_cpp->huggingface"
        m.web_search_processor = None
        return m

    def test_fallback_chain_order(self):
        """Testa se a ordem de fallback esta correta: OpenRouter -> llama_cpp."""
        manager = self.make_manager()

        async def run():
            manager._try_openrouter = AsyncMock(return_value=None)
            manager._try_llama_cpp = AsyncMock(return_value="resposta local")
            manager._try_huggingface = AsyncMock(return_value=None)

            request = Request(prompt="teste")
            result = await manager.generate(request)

            assert result == "resposta local", f"Esperado 'resposta local', obtido '{result}'"
            manager._try_openrouter.assert_awaited_once()
            manager._try_llama_cpp.assert_awaited_once()
            manager._try_huggingface.assert_not_awaited()

        asyncio.run(run())

    def test_fallback_all_fail(self):
        """Testa quando todos os backends falham."""
        manager = self.make_manager()

        async def run():
            manager._try_openrouter = AsyncMock(return_value=None)
            manager._try_llama_cpp = AsyncMock(return_value=None)
            manager._try_huggingface = AsyncMock(return_value=None)

            request = Request(prompt="teste")
            result = await manager.generate(request)

            assert "Desculpe" in result, f"Mensagem amigavel esperada, obtido '{result}'"
            manager._try_openrouter.assert_awaited_once()
            manager._try_llama_cpp.assert_awaited_once()
            manager._try_huggingface.assert_awaited_once()

        asyncio.run(run())

    def test_fallback_stream_order(self):
        """Testa fallback com streaming: OpenRouter fail -> llama_cpp stream."""
        manager = self.make_manager()

        async def mock_llama_stream(request):
            yield "token1"
            yield "token2"

        async def run():
            manager._try_openrouter_stream = AsyncMock(return_value=None)
            manager._try_llama_cpp_stream = AsyncMock(return_value=mock_llama_stream(None))
            manager._try_huggingface_stream = AsyncMock(return_value=None)

            request = Request(prompt="teste")
            tokens = []
            async for token in manager._generate_stream(request):
                tokens.append(token)

            assert tokens == ["token1", "token2"], f"Esperado ['token1', 'token2'], obtido {tokens}"
            manager._try_openrouter_stream.assert_awaited_once()
            manager._try_llama_cpp_stream.assert_awaited_once()
            manager._try_huggingface_stream.assert_not_awaited()

        asyncio.run(run())

    def test_direct_success_openrouter(self):
        """Testa quando OpenRouter responde diretamente (sem fallback)."""
        manager = self.make_manager()

        async def run():
            manager._try_openrouter = AsyncMock(return_value="resposta direta")
            manager._try_llama_cpp = AsyncMock(return_value=None)
            manager._try_huggingface = AsyncMock(return_value=None)

            request = Request(prompt="teste")
            result = await manager.generate(request)

            assert result == "resposta direta", f"Esperado 'resposta direta', obtido '{result}'"
            manager._try_openrouter.assert_awaited_once()
            manager._try_llama_cpp.assert_not_awaited()
            manager._try_huggingface.assert_not_awaited()

        asyncio.run(run())

    def test_metadata_on_fallback(self):
        """Testa se os metadados de fallback sao registrados corretamente."""
        manager = self.make_manager()

        async def run():
            manager._try_openrouter = AsyncMock(side_effect=Exception("API key invalida"))
            manager._try_llama_cpp = AsyncMock(return_value="fallback local")
            manager._try_huggingface = AsyncMock(return_value=None)

            request = Request(prompt="teste")
            result = await manager.generate(request)

            assert result == "fallback local"
            assert manager.last_fallback_triggered, "Fallback deveria estar marcado como triggered"
            assert manager.last_backend_used is not None, "Deveria registrar backend usado"

        asyncio.run(run())


if __name__ == "__main__":
    import traceback
    t = TestFallbackChain()
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
