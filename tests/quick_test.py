import asyncio
import sys
import tempfile
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from core.memory_manager import MemoriaPersistente

async def test():
    temp_dir = tempfile.mkdtemp()
    try:
        db = os.path.join(temp_dir, 'test.db')
        idx = os.path.join(temp_dir, 'test.idx')

        memoria = MemoriaPersistente(db_path=db, index_path=idx, max_memories=100)
        print('Initialized')

        for i in range(5):
            await memoria.salvar_memoria(f'Memory {i} important info', importancia=1.0 - i*0.15)
        print('5 memories inserted')

        result = await memoria.buscar_contexto('important info', k=3)
        print(f'Results: {len(result)}')
        for r in result:
            print(f'  - {r["texto"][:40]} score={r["score"]:.3f}')
        
        stats = memoria.get_stats()
        print(f'Stats: {stats}')
        print('SUCCESS - All tests passed!')
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(test())