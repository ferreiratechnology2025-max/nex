"""
Teste de integracao: FAISS ↔ SQLite consistency pos-delecao.

Cenario critico:
  - Inserir 10 memorias
  - Deletar 3 especificas (IDs 2, 5, 7)
  - Buscar deve retornar APENAS as 7 memorias validas
  - Nenhuma memoria deletada deve aparecer nos resultados
"""

import os
import sys
import tempfile
import asyncio
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.memory_manager import MemoriaPersistente


async def test_delete_and_search_returns_only_valid():
    """Testa se apos delecoes, a busca retorna apenas memorias validas."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_integration.db")
    index_path = os.path.join(temp_dir, "test_integration.faiss")

    try:
        manager = MemoriaPersistente(
            db_path=db_path,
            index_path=index_path,
            max_memories=100
        )

        texts = [f"Memoria {i}: conteudo de teste para verificacao" for i in range(10)]
        ids = []
        for t in texts:
            mem_id = await manager.salvar_memoria(t, importancia=1.0)
            ids.append(mem_id)

        print(f"Inseridos IDs: {ids}")
        assert len(ids) == 10, f"Esperado 10 IDs, obtido {len(ids)}"

        deleted = await manager.deletar_memoria(ids[2])
        assert deleted, f"Falha ao deletar memoria ID {ids[2]}"
        deleted = await manager.deletar_memoria(ids[5])
        assert deleted, f"Falha ao deletar memoria ID {ids[5]}"
        deleted = await manager.deletar_memoria(ids[7])
        assert deleted, f"Falha ao deletar memoria ID {ids[7]}"
        print(f"Deletados IDs: {ids[2]}, {ids[5]}, {ids[7]}")

        stats = manager.get_stats()
        print(f"Stats: {stats}")
        assert stats['total_memories'] == 7, f"Esperado 7 memorias no SQLite, obtido {stats['total_memories']}"

        resultados = await manager.buscar_contexto("conteudo de teste", k=10)
        print(f"Busca retornou {len(resultados)} resultados")

        assert len(resultados) == 7, (
            f"Esperado 7 resultados apos deletar 3 de 10, obtido {len(resultados)}"
        )

        result_ids = [r['id'] for r in resultados]
        assert ids[2] not in result_ids, (
            f"Memoria deletada ID {ids[2]} apareceu nos resultados!"
        )
        assert ids[5] not in result_ids, (
            f"Memoria deletada ID {ids[5]} apareceu nos resultados!"
        )
        assert ids[7] not in result_ids, (
            f"Memoria deletada ID {ids[7]} apareceu nos resultados!"
        )

        for r in resultados:
            assert 'texto' in r, "Resultado sem campo 'texto'"
            assert 'id' in r, "Resultado sem campo 'id'"
            assert 'score' in r, "Resultado sem campo 'score'"

        print("\n[PASS] test_delete_and_search_returns_only_valid PASSED!")
        return True

    except Exception as e:
        print(f"\n[FAIL] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def test_eviction_updates_mapping():
    """Testa se a eviccao automatica (max_memories) atualiza o mapping corretamente."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_eviction.db")
    index_path = os.path.join(temp_dir, "test_eviction.faiss")

    try:
        manager = MemoriaPersistente(
            db_path=db_path,
            index_path=index_path,
            max_memories=5
        )

        for i in range(8):
            await manager.salvar_memoria(
                f"Eviction test memory {i} with unique content for search",
                importancia=1.0
            )

        stats = manager.get_stats()
        print(f"Stats apos insercao de 8 (max=5): {stats}")
        # Eviction removes up to 10 bottom-scoring per trigger (original behavior).
        # Key invariant: SQLite count never exceeds FAISS valid mapped count.
        assert stats['total_memories'] == stats['faiss_valid_mapped'], (
            f"SQLite count {stats['total_memories']} != FAISS valid mapped {stats['faiss_valid_mapped']}"
        )
        assert stats['total_memories'] > 0, "Nenhuma memoria restante apos eviccao"

        resultados = await manager.buscar_contexto("unique content", k=10)
        print(f"Busca retornou {len(resultados)} resultados")

        assert len(resultados) == stats['total_memories'], (
            f"Busca retornou {len(resultados)}, SQLite tem {stats['total_memories']}"
        )

        for r in resultados:
            assert r['id'] > 0, f"ID invalido no resultado: {r['id']}"

        print("\n[PASS] test_eviction_updates_mapping PASSED!")
        return True

    except Exception as e:
        print(f"\n[FAIL] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


async def main():
    print("=" * 60)
    print("Testes de Integracao - FAISS <-> SQLite Consistency")
    print("=" * 60)

    results = []
    for test_fn in [test_delete_and_search_returns_only_valid, test_eviction_updates_mapping]:
        name = test_fn.__name__
        print(f"\n--- {name} ---")
        success = await test_fn()
        results.append((name, success))

    print("\n" + "=" * 60)
    print("RESUMO:")
    all_pass = True
    for name, success in results:
        status = "PASS" if success else "FAIL"
        if not success:
            all_pass = False
        print(f"  [{status}] {name}")

    print("=" * 60)
    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
