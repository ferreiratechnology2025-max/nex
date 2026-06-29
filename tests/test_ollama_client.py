"""
Tests for Ollama client - standalone connection and integration with LLM Manager.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ollama_client import OllamaClient, OllamaConfig
from core.llm_manager import LLMManager, Request, BackendType


PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}: {detail}")


async def test_ollama_config_defaults():
    config = OllamaConfig()
    check("default base_url", config.base_url == "http://localhost:11434")
    check("default model", config.model == "orbith:1.0")
    check("default timeout", config.timeout == 120)
    check("default temperature", config.temperature == 0.7)
    check("default top_k", config.top_k == 40)
    check("default top_p", config.top_p == 0.9)
    check("default num_ctx", config.num_ctx == 4096)


async def test_ollama_config_custom():
    config = OllamaConfig(
        base_url="http://127.0.0.1:11434",
        model="llama3.2:1b",
        timeout=60,
        temperature=0.5,
    )
    check("custom base_url", config.base_url == "http://127.0.0.1:11434")
    check("custom model", config.model == "llama3.2:1b")
    check("custom timeout", config.timeout == 60)
    check("custom temperature", config.temperature == 0.5)


async def test_ollama_client_init():
    client = OllamaClient()
    check("client created", isinstance(client, OllamaClient))
    check("session initially None", client.session is None)
    check("model initially unavailable", not client._model_available)
    await client.close()


async def test_ollama_empty_prompt_embeddings():
    """Ollama returns empty list on connection error with empty prompt."""
    config = OllamaConfig(base_url="http://localhost:99999", timeout=5)
    client = OllamaClient(config)
    async with client:
        embedding = await client.embeddings("")
    check("empty prompt returns empty", embedding == [])


async def test_ollama_connection_refused():
    """Handles connection refused gracefully."""
    config = OllamaConfig(base_url="http://localhost:99999", timeout=5)
    client = OllamaClient(config)
    async with client:
        health = await client.health_check()
    check("health returns unhealthy", health["status"] == "unhealthy")


async def test_ollama_list_models_empty():
    """List models returns empty on connection error."""
    config = OllamaConfig(base_url="http://localhost:99999", timeout=5)
    client = OllamaClient(config)
    async with client:
        models = await client.list_models()
    check("list models returns empty", models == [])


async def test_ollama_get_model_info_empty():
    """Get model info returns empty on connection error."""
    config = OllamaConfig(base_url="http://localhost:99999", timeout=5)
    client = OllamaClient(config)
    async with client:
        info = await client.get_model_info()
    check("model info returns empty", info == {})


async def test_ollama_generate_no_connection():
    """Generate returns error message on connection failure."""
    config = OllamaConfig(base_url="http://localhost:99999", timeout=5)
    client = OllamaClient(config)
    async with client:
        result = ""
        async for token in client.generate(prompt="test", max_tokens=10):
            result += token
    check("generate returns on no connection", len(result) > 0)


async def test_llm_manager_ollama_config():
    """LLMManager handles ollama_enabled config."""
    config_dict = {
        "ollama_enabled": "true",
        "OLLAMA_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "orbith:1.0",
    }
    manager = LLMManager(config=config_dict)
    check("ollama client created", manager.ollama_client is not None)
    check("ollama config model", manager.ollama_client.config.model == "orbith:1.0")
    manager.cleanup()


async def test_llm_manager_ollama_disabled():
    config_dict = {"ollama_enabled": "false"}
    manager = LLMManager(config=config_dict)
    check("ollama client is None when disabled", manager.ollama_client is None)


async def test_llm_manager_fallback_chain_includes_ollama():
    config_dict = {"ollama_enabled": "true"}
    manager = LLMManager(config=config_dict)
    check("fallback chain includes ollama", "ollama" in manager.last_fallback_chain)


async def test_backend_type_has_ollama():
    check("BackendType.OLLAMA exists", hasattr(BackendType, "OLLAMA"))
    check("BackendType.OLLAMA value", BackendType.OLLAMA == "ollama")


async def test_ollama_try_methods_exist():
    config_dict = {"ollama_enabled": "true"}
    manager = LLMManager(config=config_dict)
    check("_try_ollama exists", hasattr(manager, "_try_ollama"))
    check("_try_ollama is callable", callable(manager._try_ollama))
    check("_try_ollama_stream exists", hasattr(manager, "_try_ollama_stream"))
    check("_try_ollama_stream is callable", callable(manager._try_ollama_stream))
    manager.cleanup()


async def test_ollama_try_no_connection():
    config_dict = {"ollama_enabled": "true"}
    manager = LLMManager(config=config_dict)
    request = Request(prompt="hello")
    result = await manager._try_ollama(request)
    check("_try_ollama returns None on no connection", result is None)
    manager.cleanup()


if __name__ == "__main__":
    print("=" * 60)
    print("Testes - Cliente Ollama")
    print("=" * 60)
    print()

    tests = [
        ("test_ollama_config_defaults", test_ollama_config_defaults),
        ("test_ollama_config_custom", test_ollama_config_custom),
        ("test_ollama_client_init", test_ollama_client_init),
        ("test_ollama_empty_prompt_embeddings", test_ollama_empty_prompt_embeddings),
        ("test_ollama_connection_refused", test_ollama_connection_refused),
        ("test_ollama_list_models_empty", test_ollama_list_models_empty),
        ("test_ollama_get_model_info_empty", test_ollama_get_model_info_empty),
        ("test_ollama_generate_no_connection", test_ollama_generate_no_connection),
        ("test_llm_manager_ollama_config", test_llm_manager_ollama_config),
        ("test_llm_manager_ollama_disabled", test_llm_manager_ollama_disabled),
        ("test_llm_manager_fallback_chain_includes_ollama", test_llm_manager_fallback_chain_includes_ollama),
        ("test_backend_type_has_ollama", test_backend_type_has_ollama),
        ("test_ollama_try_methods_exist", test_ollama_try_methods_exist),
        ("test_ollama_try_no_connection", test_ollama_try_no_connection),
    ]

    for name, test_fn in tests:
        print(f"--- {name} ---")
        try:
            asyncio.run(test_fn())
        except Exception as e:
            FAIL += 1
            print(f"  [FAIL] {name}: Unhandled exception: {e}")

    print()
    print("=" * 60)
    print(f"RESUMO: {PASS} passed, {FAIL} failed")
    print("=" * 60)
