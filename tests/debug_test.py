import asyncio
import sys
import tempfile
import os
import shutil
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from core.memory_manager import MemoriaPersistente
from sentence_transformers import SentenceTransformer

async def debug_test():
    temp_dir = tempfile.mkdtemp()
    try:
        db = os.path.join(temp_dir, 'test.db')
        idx = os.path.join(temp_dir, 'test.idx')

        memoria = MemoriaPersistente(db_path=db, index_path=idx, max_memories=100)
        
        # Check dimensions
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        test_embedding = embedder.encode(['test'], convert_to_numpy=True)
        print(f'Embedder dimension: {test_embedding.shape}')
        print(f'Memoria dimension: {memoria.dimension}')
        print(f'Index ntotal: {memoria.index.ntotal}')
        print(f'Index is_trained: {memoria.index.is_trained}')
        
        # Insert
        for i in range(5):
            await memoria.salvar_memoria(f'Memory {i} important info', importancia=1.0 - i*0.15)
        
        print(f'After insert - Index ntotal: {memoria.index.ntotal}')
        
        # Check stored embeddings
        cursor = memoria.conn.execute("SELECT id, embedding_blob FROM memorias LIMIT 1")
        row = cursor.fetchone()
        if row:
            stored = pickle.loads(row[1])
            print(f'Stored embedding shape: {stored.shape}')
            print(f'Stored embedding dtype: {stored.dtype}')
        
        # Try search with correct dimensions
        query_embedding = embedder.encode(['important info'], convert_to_numpy=True)
        print(f'Query embedding shape: {query_embedding.shape}')
        
        # Search
        distances, indices = memoria.index.search(
            query_embedding.astype('float32'), 
            5
        )
        
        print(f'Indices: {indices}')
        print(f'Distances: {distances}')

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

import pickle

if __name__ == "__main__":
    asyncio.run(debug_test())