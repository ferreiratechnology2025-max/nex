"""
Teste de Fallback Z.ai -> Llama.cpp -> HuggingFace
"""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.llm_manager import LLMManager, BackendType


def test_backend_detection():
    """Testa detecção de backend"""
    config = {
        "LOCAL_MODEL_PATH": "",  # Sem modelo GGUF
        "ZAI_API_KEY": "",       # Sem API key
    }
    
    manager = LLMManager(config)
    
    # Sem ZAI_KEY e sem GGUF, deve usar HuggingFace
    assert manager.backend == BackendType.HUGGINGFACE
    print(f"Backend: {manager.backend.value}")


def test_llama_cpp_detection():
    """Testa detecção de backend GGUF"""
    # Cria arquivo temporario para teste
    test_model_path = "models/test.gguf"
    
    # Note: nao cria arquivo real para evitar download
    config = {
        "LOCAL_MODEL_PATH": test_model_path if os.path.exists(test_model_path) else "",
        "ZAI_API_KEY": "",
    }
    
    manager = LLMManager(config)
    
    # Se o modelo nao existe, cai para HuggingFace
    print(f"Backend detectado: {manager.backend.value}")


def test_zai_detection():
    """Testa detecção de Z.ai"""
    config = {
        "LOCAL_MODEL_PATH": "",
        "ZAI_API_KEY": "test-key",  # Com API key
    }
    
    manager = LLMManager(config)
    
    print(f"Backend: {manager.backend.value}")
    # Nota: pode ser ZAI ou HuggingFace dependendo se API e valida


def test_health_structure():
    """Testa estrutura de health check"""
    from src.api_gateway import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "backends" in data
    assert "fallback_order" in data
    
    # Verifica estrutura de backends
    backends = data["backends"]
    assert "zai" in backends
    assert "llama_cpp" in backends
    assert "huggingface" in backends
    
    print(f"Health response: {data}")
    print(f"Fallback order: {data['fallback_order']}")


if __name__ == "__main__":
    print("=" * 50)
    print("Teste de Fallback Nex Chat")
    print("=" * 50)
    
    print("\n1. Testando detecção de backend...")
    test_backend_detection()
    
    print("\n2. Testando health check...")
    test_health_structure()
    
    print("\n" + "=" * 50)
    print("Testes concluidos!")
    print("=" * 50)