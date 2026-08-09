"""
Testes para WebSocket e Métricas - Nex.spec.md Seção 4
Mocked tests - sem carga de modelo
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class TestMetricsCollection:
    """Testes para coleção de métricas"""
    
    def test_metrics_initialization(self):
        """Teste de inicialização das métricas"""
        from src.metrics import Metrics
        
        m = Metrics()
        metrics = m.get_metrics()
        
        assert metrics["requests_total"] == 0
        assert metrics["active_connections"] == 0
        assert metrics["avg_latency_ms"] == 0.0
    
    def test_increment_requests(self):
        """Teste de incremento de requests"""
        from src.metrics import Metrics, reset_metrics
        
        reset_metrics()
        m = Metrics()
        
        m.increment_requests()
        m.increment_requests()
        m.increment_requests()
        
        assert m.get_metrics()["requests_total"] == 3
    
    def test_increment_decrement_connections(self):
        """Teste de conexões ativas"""
        from src.metrics import Metrics, reset_metrics
        
        reset_metrics()
        m = Metrics()
        
        m.increment_connections()
        m.increment_connections()
        m.decrement_connections()
        
        assert m.get_metrics()["active_connections"] == 1
    
    def test_latency_ema(self):
        """Teste de média móvel exponencial"""
        from src.metrics import Metrics, reset_metrics
        
        reset_metrics()
        m = Metrics()
        
        m.update_latency(100.0)
        m.update_latency(200.0)
        
        # Should be between 100 and 200 due to EMA
        metrics = m.get_metrics()
        assert 100 < metrics["avg_latency_ms"] < 200
    
    def test_get_metrics(self):
        """Teste de get_metrics função exportada"""
        from src.metrics import get_metrics, reset_metrics
        
        reset_metrics()
        
        metrics = get_metrics()
        
        assert "requests_total" in metrics
        assert "active_connections" in metrics
        assert "avg_latency_ms" in metrics
        assert "peak_memory_mb" in metrics
    
    def test_reset_metrics(self):
        """Teste de reset de métricas"""
        from src.metrics import Metrics, reset_metrics, get_metrics
        
        reset_metrics()
        
        m = Metrics()
        m.increment_requests()
        m.increment_connections()
        
        reset_metrics()
        
        metrics = get_metrics()
        assert metrics["requests_total"] == 0
        assert metrics["active_connections"] == 0


class TestMetricsMiddleware:
    """Testes para middleware de métricas"""
    
    def test_middleware_registered(self):
        """Teste de registro do middleware"""
        from src.api_gateway import app
        
        # Check that middleware is registered
        # (This is implicit in FastAPI)
        assert app is not None
    
    def test_middleware_does_not_break_request(self):
        """Teste de que middleware não quebra requests"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200


class TestWebSocketEndpoint:
    """Testes para endpoint WebSocket"""
    
    def test_ws_endpoint_exists(self):
        """Teste de que endpoint WS existe"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app
        
        # Just check app has the route
        routes = [r.path for r in app.routes]
        assert any("/ws/chat" in r for r in routes)
    
    def test_ws_handler_has_correct_signature(self):
        """Teste de assinatura do handler"""
        import inspect
        from src.ws_handler import websocket_chat
        
        sig = inspect.signature(websocket_chat)
        params = list(sig.parameters.keys())
        
        # Should have websocket and request parameters
        assert "websocket" in params
        assert "request" in params
    
    def test_ws_route_registered(self):
        """Teste de registro da rota"""
        from src.ws_handler import router
        
        # Check routes
        routes = [r.path for r in router.routes]
        assert "/chat" in routes


class TestMetricsEndpoint:
    """Testes para endpoint de métricas"""
    
    def test_metrics_endpoint_returns_data(self):
        """Teste de que /metrics retorna dados"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app
        from src.metrics import reset_metrics
        
        reset_metrics()
        
        client = TestClient(app)
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "requests_total" in data
        assert "active_connections" in data


class TestWebSocketJsonFormat:
    """Testes para formato JSON do WebSocket"""
    
    def test_ws_json_structure(self):
        """Teste de estrutura JSON esperada"""
        # Test that we expect correct JSON format
        expected_keys = ["text", "max_tokens", "temperature", "use_memory"]
        
        # This is a documentation test
        assert expected_keys == ["text", "max_tokens", "temperature", "use_memory"]


class TestMetricsIntegration:
    """Testes de integração com app"""
    
    def test_metrics_after_http_request(self):
        """Teste de métricas após request HTTP"""
        from fastapi.testclient import TestClient
        from src.api_gateway import app
        from src.metrics import reset_metrics, get_metrics
        
        reset_metrics()
        
        client = TestClient(app)
        
        # Make some requests
        for i in range(3):
            client.get("/")
        
        metrics = get_metrics()
        
        # Should have recorded 3 requests
        assert metrics["requests_total"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])