"""
Configuração Centralizada - Nex.spec.md Seção 3
Settings via Pydantic com validação
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carrega .env da raiz do projeto
_root_dir = Path(__file__).parent.parent
load_dotenv(dotenv_path=_root_dir / ".env")


class Settings(BaseSettings):
    """Configurações centralizadas do projeto"""
    
    # Modelo LLM
    MODEL_NAME: str = Field(default="gemma2:2b", description="Nome do modelo")

    # Ollama Configuration (100% local)
    OLLAMA_ENABLED: bool = Field(default=True, env="OLLAMA_ENABLED")
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    OLLAMA_MODEL: str = Field(default="orbith:1.0", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(default=120, ge=30, le=600, env="OLLAMA_TIMEOUT")
    OLLAMA_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, env="OLLAMA_TEMPERATURE")
    OLLAMA_TOP_K: int = Field(default=40, ge=1, le=100, env="OLLAMA_TOP_K")
    OLLAMA_TOP_P: float = Field(default=0.9, ge=0.0, le=1.0, env="OLLAMA_TOP_P")
    OLLAMA_REPEAT_PENALTY: float = Field(default=1.1, ge=0.0, le=2.0, env="OLLAMA_REPEAT_PENALTY")
    OLLAMA_NUM_CTX: int = Field(default=4096, ge=512, le=16384, env="OLLAMA_NUM_CTX")
    OLLAMA_NUM_BATCH: int = Field(default=512, ge=1, le=2048, env="OLLAMA_NUM_BATCH")
    OLLAMA_USE_GPU: bool = Field(default=True, env="OLLAMA_USE_GPU")
    USE_OLLAMA_EMBEDDINGS: bool = Field(default=True, env="USE_OLLAMA_EMBEDDINGS")
    EMBEDDING_DIMENSION: int = Field(default=4096, ge=384, le=8192, env="EMBEDDING_DIMENSION")

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = Field(default="", env="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    OPENROUTER_MODEL: str = Field(default="openrouter/owl-alpha", env="OPENROUTER_MODEL")
    OPENROUTER_FALLBACK_MODEL: str = Field(default="nvidia/nemotron-3-nano-30b-a3b:free", env="OPENROUTER_FALLBACK_MODEL")
    WEB_SEARCH_ENABLED: bool = Field(default=True, env="WEB_SEARCH_ENABLED")
    WEB_SEARCH_MAX_RESULTS: int = Field(default=5, ge=1, le=10, env="WEB_SEARCH_MAX_RESULTS")
    WEB_SEARCH_SAVE_TO_MEMORY: bool = Field(default=True, env="WEB_SEARCH_SAVE_TO_MEMORY")

    # Backend selection
    USE_HUGGINGFACE: bool = Field(default=True, env="USE_HUGGINGFACE")

    # HuggingFace local model
    HF_MODEL_NAME: str = Field(default="microsoft/phi-2", env="HF_MODEL_NAME")
    HF_FALLBACK_MODEL: str = Field(default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", env="HF_FALLBACK_MODEL")
    HF_USE_GPU: bool = Field(default=False, env="HF_USE_GPU")
    HF_MAX_LENGTH: int = Field(default=512, ge=128, le=2048, env="HF_MAX_LENGTH")
    
    # Local LLM (llama-cpp fallback)
    LOCAL_MODEL_PATH: str = Field(default="", env="LOCAL_MODEL_PATH", description="Path para modelo GGUF")
    LOCAL_MODEL_THREADS: int = Field(default=4, ge=1, le=16, env="LOCAL_MODEL_THREADS", description="Threads para inferência local")
    LLAMA_N_CTX: int = Field(default=2048, ge=512, le=4096, env="LLAMA_N_CTX", description="Tamanho do contexto")
    LLAMA_N_GPU_LAYERS: int = Field(default=0, ge=0, le=32, env="LLAMA_N_GPU_LAYERS", description="Camadas GPU (0 = CPU)")
    LOCAL_MODEL_TIMEOUT: int = Field(default=120, ge=30, le=300, env="LOCAL_MODEL_TIMEOUT", description="Timeout para inferência local (segundos)")
    
    # Geração
    MAX_TOKENS: int = Field(default=2048, ge=1, le=4096, description="Máximo de tokens")
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura de geração")
    TOP_P: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling")
    
    # Memória
    DB_PATH: str = Field(default="data/memoria.db", description="Path do banco SQLite")
    INDEX_PATH: str = Field(default="data/memoria.index", description="Path do índice FAISS")
    CACHE_MAX_SIZE: int = Field(default=200, ge=1, description="Tamanho máximo do cache LRU")
    MEMORY_MAX_ITEMS: int = Field(default=500, ge=1, description="Máximo de memórias no banco")
    
    # Servidor
    HOST: str = Field(default="0.0.0.0", description="Host do servidor")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Porta do servidor")
    WORKERS: int = Field(default=1, ge=1, description="Número de workers")
    LIMIT_CONCURRENCY: int = Field(default=100, description="Limite de concorrência")
    BACKLOG: int = Field(default=2048, description="Backlog do uvicorn")
    TIMEOUT_KEEP_ALIVE: int = Field(default=5, description="Timeout keep-alive")
    
    # Otimização (spec 3.3)
    OMP_NUM_THREADS: int = Field(default=2, description="Threads OMP")
    MKL_NUM_THREADS: int = Field(default=2, description="Threads MKL")
    TOKENIZERS_PARALLELISM: str = Field(default="false", description="Paralelismo de tokenizers")

    # Security - Upload
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100, env="MAX_UPLOAD_SIZE_MB")
    MAX_CONTENT_CHARS: int = Field(default=50000, ge=1000, le=200000, env="MAX_CONTENT_CHARS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    @field_validator("DB_PATH", "INDEX_PATH", mode="before")
    @classmethod
    def validate_paths(cls, v):
        """Valida e normaliza paths"""
        if v:
            return str(Path(v))
        return v
    
    @field_validator("TOKENIZERS_PARALLELISM", mode="before")
    @classmethod
    def validate_tokenizers(cls, v):
        """Valida flag de tokenizers"""
        if isinstance(v, bool):
            return str(v).lower()
        return v.lower() if isinstance(v, str) else "false"


_settings: Optional[Settings] = None


def load_settings() -> Settings:
    """Carrega settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
        _ensure_directories(_settings)
    return _settings


def _ensure_directories(settings: Settings):
    """Cria diretórios necessários se não existirem"""
    base_path = Path(".")
    
    data_dir = base_path / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {data_dir}")
    
    logs_dir = base_path / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {logs_dir}")


def get_settings() -> Settings:
    """Retorna instância singleton dos settings"""
    return load_settings()


def reset_settings():
    """Reseta settings (para testing)"""
    global _settings
    _settings = None


# Alias para compatibilidade
settings = load_settings()


# Aplica otimizações ao iniciar
def apply_optimizations():
    """Aplica otimizações do sistema conforme spec 3.3"""
    s = load_settings()
    
    os.environ["OMP_NUM_THREADS"] = str(s.OMP_NUM_THREADS)
    os.environ["MKL_NUM_THREADS"] = str(s.MKL_NUM_THREADS)
    os.environ["TOKENIZERS_PARALLELISM"] = s.TOKENIZERS_PARALLELISM
    
    print(f"Applied optimizations: OMP={s.OMP_NUM_THREADS}, MKL={s.MKL_NUM_THREADS}, TOKENIZERS={s.TOKENIZERS_PARALLELISM}")