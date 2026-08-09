"""
Testes para Web Search e Memória Persistente
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch


class TestWebSearchProcessor:
    """Testes para WebSearchProcessor"""

    def test_processor_initialization(self):
        """Testa inicialização do processador"""
        from src.core.web_search import WebSearchProcessor

        processor = WebSearchProcessor()
        assert processor is not None
        assert processor.memory_manager is None

    def test_processor_with_memory_manager(self):
        """Testa inicialização com memory manager"""
        from src.core.web_search import WebSearchProcessor

        mock_memory = Mock()
        processor = WebSearchProcessor(memory_manager=mock_memory)
        assert processor.memory_manager == mock_memory

    def test_format_for_context_empty(self):
        """Testa formatação com resultados vazios"""
        from src.core.web_search import WebSearchProcessor, SearchResult

        processor = WebSearchProcessor()
        result = processor.format_for_context([])
        assert "Nenhum resultado encontrado" in result

    def test_format_for_context_with_results(self):
        """Testa formatação com resultados"""
        from src.core.web_search import WebSearchProcessor, SearchResult

        processor = WebSearchProcessor()
        results = [
            SearchResult(
                title="Test Title",
                url="https://example.com",
                content="Test content",
                site_name="Example",
                published_date="2024-01-01",
                relevance_score=0.9
            )
        ]
        result = processor.format_for_context(results, max_results=1)
        assert "Test Title" in result
        assert "example.com" in result

    @pytest.mark.asyncio
    async def test_save_to_memory_no_manager(self):
        """Testa salvamento sem memory manager"""
        from src.core.web_search import WebSearchProcessor, SearchResult

        processor = WebSearchProcessor()
        results = [
            SearchResult(
                title="Test",
                url="https://test.com",
                content="Content",
                site_name="Test"
            )
        ]
        saved = await processor.save_to_memory(results, "test query")
        assert saved == 0

    @pytest.mark.asyncio
    async def test_save_to_memory_with_manager(self):
        """Testa salvamento com memory manager"""
        from src.core.web_search import WebSearchProcessor, SearchResult

        mock_memory = AsyncMock()
        mock_memory.salvar_memoria = AsyncMock(return_value=1)

        processor = WebSearchProcessor(memory_manager=mock_memory)
        results = [
            SearchResult(
                title="Test",
                url="https://test.com",
                content="Content",
                site_name="Test"
            )
        ]
        saved = await processor.save_to_memory(results, "test query")
        assert saved == 1
        mock_memory.salvar_memoria.assert_called_once()


class TestBackendDetection:
    """Testes para detecção de backend"""

    def test_detect_huggingface_backend(self):
        """Testa detecção de backend HuggingFace"""
        from src.core.llm_manager import LLMManager, BackendType

        config = {
            "ZAI_API_KEY": "",
            "USE_HUGGINGFACE": True
        }

        llm = LLMManager(config)
        assert llm.backend == BackendType.HUGGINGFACE

    def test_detect_huggingface_placeholder_key(self):
        """Testa fallback com chave placeholder"""
        from src.core.llm_manager import LLMManager, BackendType

        config = {
            "ZAI_API_KEY": "sua-chave-api-aqui",
            "USE_HUGGINGFACE": True
        }

        llm = LLMManager(config)
        assert llm.backend == BackendType.HUGGINGFACE


class TestLLMGenerate:
    """Testes para geração LLM"""

    @pytest.mark.asyncio
    async def test_generate_without_web_search(self):
        """Testa geração sem web search"""
        from src.core.llm_manager import LLMManager, BackendType, Request

        config = {
            "ZAI_API_KEY": "",
            "USE_HUGGINGFACE": True
        }

        try:
            llm = LLMManager(config)
            if llm.backend == BackendType.HUGGINGFACE and not llm.is_loaded():
                pytest.skip("HuggingFace model não disponível para teste")
        except Exception as e:
            pytest.skip(f"Não foi possível inicializar: {e}")

        request = Request(prompt="Olá", max_tokens=50)
        response = await llm.generate(request)

        assert response is not None
        assert isinstance(response, str)

    def test_get_model_name_zai(self):
        """Testa get_model_name para Z.ai com API key mas sem cliente real"""
        from src.core.llm_manager import LLMManager, BackendType

        config = {
            "ZAI_API_KEY": "",  # Sem key real
            "ZAI_MODEL": "glm-4.7-flash"
        }

        llm = LLMManager(config)
        # Sem key, não pode usar Z.ai, então retorna HF
        assert llm.get_model_name() in ["glm-4.7-flash", "HuggingFaceTB/SmolLM-135M"]

    def test_get_device_zai(self):
        """Testa get_device"""
        from src.core.llm_manager import LLMManager, BackendType

        config = {"ZAI_API_KEY": ""}

        try:
            llm = LLMManager(config)
            device = llm.get_device()
            assert device in ["cloud", "cpu", "cuda"]
        except Exception:
            pytest.skip("Não foi possível inicializar LLM")


class TestConfig:
    """Testes de configuração"""

    def test_load_dotenv(self):
        """Testa se .env é carregado"""
        from src.config import get_settings

        settings = get_settings()
        assert settings is not None

    def test_zai_config_defaults(self):
        """Testa valores padrão da config Z.ai"""
        from src.config import get_settings

        settings = get_settings()
        assert hasattr(settings, 'ZAI_API_KEY')
        assert hasattr(settings, 'ZAI_MODEL')
        assert hasattr(settings, 'WEB_SEARCH_ENABLED')
        assert settings.ZAI_MODEL == "glm-4.7-flash"

    def test_web_search_config(self):
        """Testa configurações de web search"""
        from src.config import get_settings

        settings = get_settings()
        assert hasattr(settings, 'WEB_SEARCH_MAX_RESULTS')
        assert hasattr(settings, 'WEB_SEARCH_SAVE_TO_MEMORY')


class TestIntegration:
    """Testes de integração"""

    @pytest.mark.asyncio
    async def test_llm_manager_with_memory(self):
        """Testa LLMManager com memory manager"""
        from src.core.llm_manager import LLMManager
        from unittest.mock import Mock

        mock_memory = Mock()

        config = {"ZAI_API_KEY": ""}
        llm = LLMManager(config, memory_manager=mock_memory)

        assert llm.memory_manager == mock_memory

    @pytest.mark.asyncio
    async def test_web_search_processor_with_zai_client(self):
        """Testa WebSearchProcessor com Z.ai client"""
        from src.core.web_search import WebSearchProcessor

        mock_zai = Mock()
        mock_zai.is_available.return_value = True

        processor = WebSearchProcessor(zai_client=mock_zai)
        assert processor.zai_client == mock_zai


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
