"""
Sistema de Memoria Otimizado - Nex.spec.md Seção 2.1
Cache LRU + SQLite WAL + FAISS HNSW + Fila Sincrona de Embeddings
"""

import asyncio
import sqlite3
import pickle
import logging
import queue
import threading
import os
from collections import OrderedDict
from typing import List, Dict, Optional
from concurrent.futures import Future as ConcurrentFuture
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class MemoriaItem:
    texto: str
    embedding: np.ndarray
    timestamp: float
    importancia: float = 1.0
    acessos: int = 0


class CacheLRU:
    """Cache com LRU + TTL para embeddings"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[np.ndarray]:
        async with self._lock:
            if key not in self._cache:
                return None

            if datetime.now(timezone.utc).timestamp() - self._timestamps[key] > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None

            self._cache.move_to_end(key)
            return self._cache[key]

    async def set(self, key: str, value):
        async with self._lock:
            if len(self._cache) >= self.max_size:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
                del self._timestamps[oldest]

            self._cache[key] = value
            self._timestamps[key] = datetime.now(timezone.utc).timestamp()
            self._cache.move_to_end(key)

    async def clear(self):
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()


class MemoriaPersistente:
    """Sistema de memoria com SQLite + FAISS otimizado.

    Mantem um mapping explicito _faiss_to_db entre posicoes do FAISS e IDs
    do SQLite para garantir consistencia mesmo apos delecoes.
    """

    def __init__(self, db_path: str,
                 index_path: str,
                 max_memories: int = 500,
                 ollama_client=None):

        self.db_path = db_path
        self.index_path = index_path
        self.max_memories = max_memories
        self.ollama_client = ollama_client

        self.cache_lru = CacheLRU(max_size=100, ttl=1800)
        self._db_lock = asyncio.Lock()
        self.embedding_dim = 4096 if ollama_client else 384

        self._init_sqlite()
        self._init_faiss()

        self._worker_ready = threading.Event()
        self.embedder = None
        self.embedding_queue = queue.Queue(maxsize=100)

        self.embedding_worker = threading.Thread(
            target=self._run_embedding_worker,
            daemon=True
        )
        self.embedding_worker.start()

    def _init_sqlite(self):
        """Schema otimizado com indices e WAL mode"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=10000")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                embedding_blob BLOB,
                timestamp REAL NOT NULL,
                importancia REAL DEFAULT 1.0,
                acessos INTEGER DEFAULT 0,
                sumario TEXT,
                tags TEXT
            )
        """)

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memorias(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_importancia ON memorias(importancia DESC)")
        self.conn.commit()

    def _init_faiss(self):
        """FAISS com indice HNSW + mapping FAISS->SQLite para consistencia pos-delecao."""
        logger = logging.getLogger(__name__)
        self._faiss_to_db: List[Optional[int]] = []

        try:
            import faiss

            self.dimension = self.embedding_dim

            if os.path.exists(self.index_path):
                try:
                    self.index = faiss.read_index(self.index_path)

                    if self.index.d != self.embedding_dim:
                        logger.warning(
                            f"FAISS dimension mismatch: {self.index.d} != {self.embedding_dim}. "
                            "Criando novo indice."
                        )
                        self.index = faiss.IndexHNSWFlat(self.dimension, 32)
                    else:
                        logger.info(
                            f"Indice FAISS HNSW carregado: {self.index.ntotal} vetores, "
                            f"dimensao {self.index.d}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to load FAISS index: {e}. Criando novo indice.")
                    self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                logger.info("Nenhum indice FAISS encontrado. Criando novo HNSW.")
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)

            faiss_count = self.index.ntotal

            cursor = self.conn.execute("SELECT id FROM memorias ORDER BY id")
            db_ids = [row[0] for row in cursor.fetchall()]

            self._faiss_to_db = db_ids[:faiss_count]
            if len(self._faiss_to_db) < faiss_count:
                self._faiss_to_db.extend([None] * (faiss_count - len(self._faiss_to_db)))

        except ImportError:
            logger.warning("FAISS not available. Vector search disabled.")
            self.index = None
            self.dimension = self.embedding_dim

    def _run_embedding_worker(self):
        """Worker sincrono de embeddings em thread separada."""
        try:
            from sentence_transformers import SentenceTransformer

            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedder.to('cpu')
            self._worker_ready.set()

            while True:
                try:
                    item = self.embedding_queue.get(timeout=1)
                    if item is None:
                        break

                    text, future = item
                    embedding = self.embedder.encode(
                        [text],
                        show_progress_bar=False,
                        convert_to_numpy=True
                    )
                    if not future.done():
                        future.set_result(embedding[0])
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Erro embedding: {e}")

        except ImportError:
            print("sentence-transformers not available")
            self._worker_ready.set()
        except Exception as e:
            print(f"Erro ao iniciar worker: {e}")
            self._worker_ready.set()

    async def _get_embedder(self):
        """Retorna o embedder, aguardando sem bloquear o event loop."""
        if self.embedder is not None:
            return self.embedder
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._worker_ready.wait)
        return self.embedder

    async def _get_embedding(self, text: str) -> np.ndarray:
        if self.ollama_client is not None:
            try:
                vec = await self.ollama_client.embeddings(text)
                if vec and len(vec) == self.dimension:
                    logger.debug(f"Embedding via Ollama: {len(vec)} dims")
                    return np.array(vec, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Ollama embedding failed: {e}")
        future_embedding: ConcurrentFuture = ConcurrentFuture()
        self.embedding_queue.put((text, future_embedding))
        try:
            return await asyncio.wait_for(
                asyncio.wrap_future(future_embedding), timeout=30.0
            )
        except (asyncio.TimeoutError, TimeoutError):
            logger.warning("Embedding timeout, using zeroed vector")
            return np.zeros(self.dimension, dtype=np.float32)

    async def salvar_memoria(self, texto: str, importancia: float = 1.0) -> int:
        logger = logging.getLogger(__name__)

        embedding = await self._get_embedding(texto)

        async with self._db_lock:
            try:
                cursor = self.conn.execute("SELECT COUNT(*) FROM memorias")
                count = cursor.fetchone()[0]

                if count >= self.max_memories:
                    cursor = self.conn.execute("""
                        SELECT id FROM memorias
                        ORDER BY importancia * LOG(acessos + 1) ASC
                        LIMIT 10
                    """)
                    evict_ids = {row[0] for row in cursor.fetchall()}

                    placeholders = ','.join(['?'] * len(evict_ids))
                    self.conn.execute(
                        f"DELETE FROM memorias WHERE id IN ({placeholders})",
                        list(evict_ids)
                    )

                    if self.index is not None:
                        for i in range(len(self._faiss_to_db)):
                            if self._faiss_to_db[i] in evict_ids:
                                self._faiss_to_db[i] = None

                timestamp = datetime.now(timezone.utc).timestamp()

                if self.index is not None and embedding is not None:
                    try:
                        import faiss
                        self.index.add(np.array([embedding]).astype('float32'))
                    except Exception as e:
                        logger.error(f"FAISS add failed: {e}")
                        raise

                cursor = self.conn.execute("""
                    INSERT INTO memorias (texto, embedding_blob, timestamp, importancia)
                    VALUES (?, ?, ?, ?)
                """, (texto, pickle.dumps(embedding), timestamp, importancia))

                self.conn.commit()

                if self.index is not None:
                    new_id = cursor.lastrowid
                    self._faiss_to_db.append(new_id)
                    try:
                        import faiss
                        faiss.write_index(self.index, self.index_path)
                    except Exception as e:
                        logger.warning(f"FAISS disk save failed (in-memory OK): {e}")

                return cursor.lastrowid

            except Exception as e:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                logger.error(f"Rollback applied em salvar_memoria: {e}")
                raise

    async def buscar_contexto(self, query: str, k: int = 5) -> List[Dict]:
        """Busca contexto com cache e re-ranking.

        Usa o mapping _faiss_to_db para traduzir posicoes do FAISS em IDs
        reais do SQLite, garantindo que memorias deletadas nunca sejam retornadas.
        """
        async with self._db_lock:
            cache_key = f"{query}_{k}"
            cached = await self.cache_lru.get(cache_key)
            if cached is not None:
                return cached

        embedder = await self._get_embedder()
        if embedder is None:
            return []

        loop = asyncio.get_event_loop()
        try:
            query_embedding = await loop.run_in_executor(
                None,
                lambda: embedder.encode([query], convert_to_numpy=True)[0]
            )
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

        resultados = []

        if self.index is not None and self.index.ntotal > 0:
            k_search = k * 3
            try:
                search_vector = np.array([query_embedding]).astype('float32')
                distances, indices = self.index.search(search_vector, k_search)

                for faiss_pos, dist in zip(indices[0], distances[0]):
                    if faiss_pos == -1:
                        continue

                    if faiss_pos >= len(self._faiss_to_db):
                        continue

                    db_id = self._faiss_to_db[faiss_pos]
                    if db_id is None:
                        continue

                    cursor = self.conn.execute(
                        "SELECT id, texto, importancia FROM memorias WHERE id = ?",
                        (db_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        self.conn.execute(
                            "UPDATE memorias SET acessos = acessos + 1 WHERE id = ?",
                            (row[0],)
                        )

                        resultados.append({
                            'id': row[0],
                            'texto': row[1],
                            'importancia': row[2],
                            'distancia': float(dist),
                            'score': 1.0 / (1.0 + dist)
                        })
            except Exception as e:
                print(f"Error in FAISS search: {e}")

        resultados.sort(key=lambda x: x['score'], reverse=True)
        result = resultados[:k]

        await self.cache_lru.set(cache_key, result)

        return result

    async def deletar_memoria(self, memoria_id: int) -> bool:
        """Remove a memory by ID and marks its FAISS mapping entry as invalid.

        The FAISS position is preserved (HNSW indices do not support removal),
        but _faiss_to_db is marked as None, ensuring buscar_contexto never
        returns this memory.
        """
        async with self._db_lock:
            cursor = self.conn.execute("DELETE FROM memorias WHERE id = ?", (memoria_id,))
            if cursor.rowcount == 0:
                return False

            if self.index is not None:
                for i in range(len(self._faiss_to_db)):
                    if self._faiss_to_db[i] == memoria_id:
                        self._faiss_to_db[i] = None
                        break

            self.conn.commit()
            return True

    def get_stats(self) -> Dict:
        """Retorna estatisticas do sistema"""
        cursor = self.conn.execute("SELECT COUNT(*) FROM memorias")
        total = cursor.fetchone()[0]

        faiss_count = self.index.ntotal if self.index is not None else 0
        valid_mapped = sum(1 for x in self._faiss_to_db if x is not None) if hasattr(self, '_faiss_to_db') else 0

        return {
            'total_memories': total,
            'faiss_vectors': faiss_count,
            'faiss_valid_mapped': valid_mapped,
            'cache_size': len(self.cache_lru._cache),
        }

    def __del__(self):
        if hasattr(self, 'conn'):
            try:
                self.conn.close()
            except Exception:
                pass


# Alias para compatibilidade
MemoryManager = MemoriaPersistente