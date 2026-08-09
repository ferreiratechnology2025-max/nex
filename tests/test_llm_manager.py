"""
Testes para LLM Manager - Nex.spec.md Seção 2.2
KV Cache + Dynamic Batching
"""

import os
import sys
import asyncio
import unittest
import gc
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class TestLLMManager(unittest.TestCase):
    """Testes para LLM Manager"""
    
    def test_request_dataclass(self):
        """Teste do dataclass Request"""
        from core.llm_manager import Request
        
        req = Request(
            prompt="Hello",
            max_tokens=100,
            temperature=0.8,
            top_p=0.9,
            stream=False
        )
        
        self.assertEqual(req.prompt, "Hello")
        self.assertEqual(req.max_tokens, 100)
        self.assertEqual(req.temperature, 0.8)
        self.assertEqual(req.top_p, 0.9)
        self.assertFalse(req.stream)
    
    def test_initialization(self):
        """Teste de inicialização"""
        from core.llm_manager import LLMManager
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        self.assertIsNotNone(manager.model_name)
        self.assertIn(manager.device, ["cuda", "cpu"])
        self.assertIsNotNone(manager.request_queue)
    
    def test_model_loaded(self):
        """Teste de verificação de modelo carregado"""
        from core.llm_manager import LLMManager
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        self.assertTrue(manager.is_loaded())
        self.assertEqual(manager.get_device(), manager.device)
        self.assertEqual(manager.get_model_name(), "HuggingFaceTB/SmolLM-135M")
    
    def test_cleanup(self):
        """Teste de cleanup de memória"""
        from core.llm_manager import LLMManager
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        manager.cleanup()
        
        self.assertFalse(manager.is_loaded())


class TestBatching(unittest.TestCase):
    """Testes para dynamic batching"""
    
    def setUp(self):
        """Setup com modelo leve para teste"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Cleanup"""
        gc.collect()
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def test_batch_processing(self):
        """Teste de processamento em batch"""
        from core.llm_manager import LLMManager, Request
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        self.assertTrue(manager.is_loaded())
        
        requests = [
            Request(prompt="Say hello", max_tokens=20),
            Request(prompt="Say world", max_tokens=20),
            Request(prompt="Say test", max_tokens=20),
        ]
        
        async def run_batch():
            results = []
            for req in requests:
                result = await manager.generate(req)
                results.append(result)
            return results
        
        results = asyncio.run(run_batch())
        
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, str)
        
        manager.cleanup()
    
    def test_single_request(self):
        """Teste de request único"""
        from core.llm_manager import LLMManager, Request
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        req = Request(prompt="What is 2+2?", max_tokens=30)
        
        async def run_single():
            return await manager.generate(req)
        
        result = asyncio.run(run_single())
        
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        
        manager.cleanup()


class TestCPUFallback(unittest.TestCase):
    """Testes para fallback CPU"""
    
    def test_cpu_fallback_on_no_cuda(self):
        """Teste de fallback para CPU quando não há CUDA"""
        import torch
        
        original_cuda = torch.cuda.is_available
        
        try:
            torch.cuda.is_available = lambda: False
            
            from core.llm_manager import LLMManager
            
            manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
            
            self.assertEqual(manager.get_device(), "cpu")
            self.assertTrue(manager.is_loaded())
            
            manager.cleanup()
            
        finally:
            torch.cuda.is_available = original_cuda


class TestMemoryCleanup(unittest.TestCase):
    """Testes para cleanup de memória"""
    
    def test_memory_cleanup(self):
        """Teste de liberação de memória"""
        import torch
        import gc
        
        from core.llm_manager import LLMManager
        
        manager = LLMManager(model_name="HuggingFaceTB/SmolLM-135M")
        
        self.assertTrue(manager.is_loaded())
        
        initial_objects = len(gc.get_objects())
        
        manager.cleanup()
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        final_objects = len(gc.get_objects())
        
        self.assertFalse(manager.is_loaded())


if __name__ == "__main__":
    print("=" * 50)
    print("Testes - LLM Manager")
    print("=" * 50)
    
    unittest.main(exit=False)