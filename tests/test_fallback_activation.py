import unittest
from unittest.mock import patch


class TestFallbackActivation(unittest.IsolatedAsyncioTestCase):
    async def test_llm_manager_fallback_to_llama_cpp(self):
        from src.core.llm_manager import LLMManager, Request, BackendType
        from src.metrics import metrics

        with (
            patch.object(LLMManager, "_init_huggingface", lambda self: setattr(self, "_loaded", False)),
            patch.object(LLMManager, "_init_zai", lambda self: None),
            patch.object(LLMManager, "_init_llama_cpp", lambda self: None),
            patch.object(LLMManager, "_detect_backend", lambda self: BackendType.ZAI),
        ):
            manager = LLMManager(config={"USE_HUGGINGFACE": "false"})

        class _StubZai:
            def is_available(self):
                return True

        manager._zai_client = _StubZai()

        async def _fail_zai(*args, **kwargs):
            raise Exception("API error 429: rate limit")

        with (
            patch.object(manager, "_generate_zai", _fail_zai),
            patch.object(manager, "can_use_llama_cpp", lambda: True),
            patch.object(manager, "_load_llama_cpp_model_for_fallback", lambda: setattr(manager, "_local_llm", object()) or True),
            patch.object(manager, "_generate_llama_cpp", lambda *args, **kwargs: "ok-llama"),
        ):
            before = metrics.get_metrics()["llm_fallback_total"]
            resp = await manager.generate(Request(prompt="hi", max_tokens=5))
            after = metrics.get_metrics()["llm_fallback_total"]

        self.assertEqual(resp, "ok-llama")
        self.assertEqual(manager.last_backend_used, BackendType.LLAMA_CPP)
        self.assertTrue(manager.last_fallback_triggered)
        self.assertEqual(after, before + 1)

    def test_api_ask_sets_fallback_headers(self):
        from fastapi.testclient import TestClient

        from src.api_gateway import app, RateLimiter
        from src.core.llm_manager import LLMManager, BackendType

        with (
            patch.object(LLMManager, "_init_huggingface", lambda self: setattr(self, "_loaded", False)),
            patch.object(LLMManager, "_init_zai", lambda self: None),
            patch.object(LLMManager, "_init_llama_cpp", lambda self: None),
            patch.object(LLMManager, "_detect_backend", lambda self: BackendType.ZAI),
        ):
            manager = LLMManager(config={"USE_HUGGINGFACE": "false"})

        class _StubZai:
            def is_available(self):
                return True

        manager._zai_client = _StubZai()

        async def _fail_zai(*args, **kwargs):
            raise Exception("Request timeout")

        with (
            patch.object(manager, "_generate_zai", _fail_zai),
            patch.object(manager, "can_use_llama_cpp", lambda: True),
            patch.object(manager, "_load_llama_cpp_model_for_fallback", lambda: setattr(manager, "_local_llm", object()) or True),
            patch.object(manager, "_generate_llama_cpp", lambda *args, **kwargs: "ok-llama"),
        ):
            app.state.llm_manager = manager
            app.state.rate_limiter = RateLimiter(requests_per_minute=1000)

            client = TestClient(app)
            r = client.post("/ask", json={"text": "teste", "use_memory": False, "stream": False})

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("X-Backend-Used"), "llama_cpp")
        self.assertEqual(r.headers.get("X-Fallback-Triggered"), "true")
        self.assertEqual(r.headers.get("X-Fallback-Chain"), "zai->llama_cpp->huggingface")
