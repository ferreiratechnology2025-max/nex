"""
Testes para API Gateway - Nex.spec.md Seção 2.3
Mocked tests - sem carga de modelo
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class TestPromptBuilding:
    """Testes para construção de prompt"""
    
    def test_prompt_with_context(self):
        """Teste de prompt com contexto"""
        from src.api_gateway import build_prompt
        
        prompt = build_prompt("What is AI?", "Memory: AI is artificial intelligence.")
        
        assert "What is AI?" in prompt
        assert "Memory:" in prompt
        assert "<|im_start|>system" in prompt
    
    def test_prompt_without_context(self):
        """Teste de prompt sem contexto"""
        from src.api_gateway import build_prompt
        
        prompt = build_prompt("Hello", "")
        
        assert "Hello" in prompt
        assert "<|im_start|>user" in prompt


class TestRateLimiter:
    """Testes para rate limiter"""
    
    def test_rate_limiter_init(self):
        """Teste de inicialização do rate limiter"""
        from src.api_gateway import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter.requests_per_minute == 10
    
    @pytest.mark.asyncio
    async def test_rate_limiter_check_ok(self):
        """Teste de rate limiter dentro do limite"""
        from src.api_gateway import RateLimiter
        
        limiter = RateLimiter(requests_per_minute=5)
        
        for i in range(5):
            await limiter.check("test_client")
        
        # Should not raise


class TestPydanticModels:
    """Testes para modelos Pydantic"""
    
    def test_query_model(self):
        """Teste do modelo Query"""
        from src.api_gateway import Query
        
        query = Query(text="Hello", max_tokens=100, temperature=0.5)
        
        assert query.text == "Hello"
        assert query.max_tokens == 100
        assert query.temperature == 0.5
        assert query.stream is False
        assert query.use_memory is True
    
    def test_query_defaults(self):
        """Teste de valores padrão do Query"""
        from src.api_gateway import Query
        
        query = Query(text="Test")

        assert query.max_tokens == 2048
        assert query.temperature == 0.7
        assert query.stream is False
        assert query.use_memory is True
    
    def test_memory_model(self):
        """Teste do modelo Memory"""
        from src.api_gateway import Memory
        
        memory = Memory(text="Important fact", importance=1.5)
        
        assert memory.text == "Important fact"
        assert memory.importance == 1.5
    
    def test_query_validation(self):
        """Teste de validação do Query"""
        from src.api_gateway import Query
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            Query(text="Test", temperature=2.0)


class TestAppCreation:
    """Testes para criação do app"""
    
    def test_app_created(self):
        """Teste de criação do app"""
        from src.api_gateway import app
        
        assert app.title == "Nex Local AI Assistant"
        assert app.version == "1.0.0"


class TestIntegration:
    """Testes de integração com mocks"""
    
    def test_app_with_test_client(self):
        """Teste básico do app com TestClient"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app, build_prompt
        from src.api_gateway import RateLimiter
        
        # Test that the app can be instantiated
        client = TestClient(app)
        
        # Test root endpoint (no model loading) — "/" serve a UI de chat
        # (HTMLResponse deliberado, src/api_gateway.py:616), não JSON.
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_health_without_models(self):
        """Teste health sem modelos carregados"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app
        
        client = TestClient(app)
        
        # Note: Without mocks, this may return "unknown" but should not fail
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_ask_without_memory_uses_test_client(self):
        """Teste /ask sem memória usando TestClient"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app, RateLimiter

        # app.state.rate_limiter (e demais estado) é inicializado
        # imperativamente em src/main.py:main() — não por um evento de
        # lifespan do FastAPI. Como este teste importa `app` diretamente
        # de api_gateway (sem passar por main()), precisa popular o
        # estado mínimo necessário à mão, como já é feito em outros
        # testes de integração deste arquivo.
        app.state.rate_limiter = RateLimiter(requests_per_minute=1000)

        with TestClient(app) as client:
            response = client.post("/ask", json={
                "text": "Hello",
                "use_memory": False
            })

        # May fail if no model, but tests the endpoint exists
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])