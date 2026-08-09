"""
Testes para Módulo de Memória Otimizada - Nex.spec.md Seção 2.1
"""

import os
import sys
import tempfile
import asyncio
import unittest
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.memory_manager import MemoriaPersistente, CacheLRU


class TestCacheLRU(unittest.TestCase):
    """Testes para o Cache LRU"""
    
    def test_cache_set_get(self):
        """Teste básico de set/get"""
        cache = CacheLRU(max_size=3, ttl=60)
        
        import numpy as np
        arr = np.array([1, 2, 3])
        
        cache.set("key1", arr)
        result = cache.get("key1")
        
        self.assertIsNotNone(result)
        self.assertTrue(np.array_equal(result, arr))
    
    def test_cache_miss(self):
        """Teste de cache miss"""
        cache = CacheLRU(max_size=3, ttl=60)
        result = cache.get("nonexistent")
        self.assertIsNone(result)
    
    def test_cache_eviction(self):
        """Teste de eviction LRU"""
        cache = CacheLRU(max_size=2, ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        self.assertIsNone(cache.get("key1"))
        self.assertIsNotNone(cache.get("key2"))
        self.assertIsNotNone(cache.get("key3"))
    
    def test_cache_ttl(self):
        """Teste de expiração por TTL"""
        import time
        cache = CacheLRU(max_size=3, ttl=1)
        
        cache.set("key1", "value1")
        time.sleep(1.5)
        
        result = cache.get("key1")
        self.assertIsNone(result)


class TestMemoriaPersistente(unittest.TestCase):
    """Testes para Memória Persistente"""
    
    def setUp(self):
        """Setup com diretório temporário"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_memoria.db")
        self.index_path = os.path.join(self.temp_dir, "test_index.faiss")
    
    def tearDown(self):
        """Cleanup"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_inicializacao(self):
        """Teste de inicialização do SQLite"""
        memoria = MemoriaPersistente(
            db_path=self.db_path,
            index_path=self.index_path,
            max_memories=100
        )
        
        cursor = memoria.conn.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        
        self.assertEqual(mode, 'wal')
        
        cursor = memoria.conn.execute("SELECT COUNT(*) FROM memorias")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
    
    def test_salvar_memoria(self):
        """Teste de salvamento de memória"""
        memoria = MemoriaPersistente(
            db_path=self.db_path,
            index_path=self.index_path,
            max_memories=100
        )
        
        id1 = asyncio.run(memoria.salvar_memoria("Primeira memória", importancia=1.0))
        id2 = asyncio.run(memoria.salvar_memoria("Segunda memória", importancia=0.5))
        
        self.assertIsNotNone(id1)
        self.assertIsNotNone(id2)
        self.assertNotEqual(id1, id2)
    
    def test_cache_lru_interno(self):
        """Teste de funcionamento do cache LRU interno"""
        memoria = MemoriaPersistente(
            db_path=self.db_path,
            index_path=self.index_path,
            max_memories=100
        )
        
        import numpy as np
        arr = np.array([1.0, 2.0, 3.0])
        
        memoria.cache_lru.set("test_key", arr)
        result = memoria.cache_lru.get("test_key")
        
        self.assertIsNotNone(result)
        self.assertTrue(np.array_equal(result, arr))


async def run_integration_test():
    """Teste de integração completo"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "integration_test.db")
    index_path = os.path.join(temp_dir, "integration_test.faiss")
    
    try:
        memoria = MemoriaPersistente(
            db_path=db_path,
            index_path=index_path,
            max_memories=100
        )
        
        print("Inserindo 5 memórias...")
        for i in range(5):
            importancia = 1.0 - (i * 0.15)
            await memoria.salvar_memoria(
                f"Memória número {i} com informação importante",
                importancia=importancia
            )
        
        print("Buscando contexto...")
        resultados = await memoria.buscar_contexto("informação importante", k=3)
        
        print(f"Resultados encontrados: {len(resultados)}")
        for r in resultados:
            print(f"  - {r['texto'][:50]}... (score: {r['score']:.3f})")
        
        stats = memoria.get_stats()
        print(f"Estatísticas: {stats}")
        
        assert len(resultados) > 0, "Deveria retornar resultados"
        
        print("\n[OK] Integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 50)
    print("Testes - Módulo de Memória Otimizada")
    print("=" * 50)
    
    unittest.main(exit=False)
    
    print("\n" + "=" * 50)
    print("Teste de Integração")
    print("=" * 50)
    
    success = asyncio.run(run_integration_test())
    
    sys.exit(0 if success else 1)