"""
Main Entry Point - Nex.spec.md Seção 3
Ponto de entrada unificado com configurações centralizadas
"""

import os
import sys
import signal
import asyncio
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Apply optimizations before any imports
from src.config import load_settings, apply_optimizations

apply_optimizations()


def setup_signal_handlers(server):
    """Configura handlers para shutdown graceful"""
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        server.should_exit = True
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Ponto de entrada principal"""
    settings = load_settings()
    
    print("=" * 60)
    print("Nex Local AI Assistant")
    print("=" * 60)
    print(f"Model: {settings.MODEL_NAME}")
    print(f"Max Tokens: {settings.MAX_TOKENS}")
    print(f"DB Path: {settings.DB_PATH}")
    print(f"Host: {settings.HOST}:{settings.PORT}")
    print("=" * 60)

    # Import after optimizations are applied
    from src.api_gateway import app
    from src.core.memory_manager import MemoriaPersistente
    from src.core.llm_manager import LLMManager
    from src.core.llm_manager import BackendType
    from src.core.document_reader import DocumentReader
    from src.core.document_manager import DocumentManager

    # Initialize memory system
    print("Initializing memory system...")
    memory_system = MemoriaPersistente(
        db_path=settings.DB_PATH,
        index_path=settings.INDEX_PATH,
        max_memories=settings.MEMORY_MAX_ITEMS
    )

    # Inject memory system into app state
    app.state.memory_system = memory_system

    # Initialize RateLimiter
    from src.api_gateway import RateLimiter
    app.state.rate_limiter = RateLimiter(requests_per_minute=100)
    print("Rate limiter initialized")

    # Initialize LLM Manager with multi-backend support
    print("Initializing LLM manager...")
    try:
        config = {
            "MODEL_NAME": settings.MODEL_NAME,
            "ollama_enabled": str(settings.OLLAMA_ENABLED),
            "OLLAMA_URL": settings.OLLAMA_URL,
            "OLLAMA_MODEL": settings.OLLAMA_MODEL,
            "OLLAMA_TIMEOUT": str(settings.OLLAMA_TIMEOUT),
            "OLLAMA_TEMPERATURE": str(settings.OLLAMA_TEMPERATURE),
            "OLLAMA_TOP_K": str(settings.OLLAMA_TOP_K),
            "OLLAMA_TOP_P": str(settings.OLLAMA_TOP_P),
            "OLLAMA_REPEAT_PENALTY": str(settings.OLLAMA_REPEAT_PENALTY),
            "OLLAMA_NUM_CTX": str(settings.OLLAMA_NUM_CTX),
            "OLLAMA_NUM_BATCH": str(settings.OLLAMA_NUM_BATCH),
            "OLLAMA_USE_GPU": str(settings.OLLAMA_USE_GPU),
            "OPENROUTER_API_KEY": settings.OPENROUTER_API_KEY,
            "OPENROUTER_MODEL": settings.OPENROUTER_MODEL,
            "OPENROUTER_FALLBACK_MODEL": settings.OPENROUTER_FALLBACK_MODEL,
            "HF_MODEL_NAME": settings.HF_MODEL_NAME,
            "HF_FALLBACK_MODEL": settings.HF_FALLBACK_MODEL,
            "HF_USE_GPU": str(settings.HF_USE_GPU),
            "HF_MAX_LENGTH": str(settings.HF_MAX_LENGTH),
            "WEB_SEARCH_ENABLED": str(settings.WEB_SEARCH_ENABLED),
            "USE_HUGGINGFACE": str(settings.USE_HUGGINGFACE)
        }
        llm_manager = LLMManager(config, memory_manager=memory_system)
        app.state.llm_manager = llm_manager

        print(f"Backend ativo: {llm_manager.backend.value}")

    except Exception as e:
        print(f"Warning: Could not initialize LLM manager: {e}")
        app.state.llm_manager = None
    
    # Initialize document system
    print("Initializing document system...")
    try:
        app.state.document_reader = DocumentReader()
        app.state.document_manager = DocumentManager(memory_system)
        print("Document system ready")
    except Exception as e:
        print(f"Warning: Could not initialize document system: {e}")
        app.state.document_reader = None
        app.state.document_manager = None
    
    # Initialize agent coordinator
    print("Initializing agent coordinator...")
    try:
        from src.agents import Coordinator
        wsp = getattr(llm_manager, "web_search_processor", None)
        app.state.coordinator = Coordinator(
            llm_manager=llm_manager,
            memory_manager=memory_system,
            web_search_processor=wsp,
            document_manager=app.state.document_manager,
        )
        print("Agent coordinator ready (LangGraph)")
    except Exception as e:
        print(f"Warning: Could not initialize coordinator: {e}")
        app.state.coordinator = None
    
    # Configure uvicorn
    import uvicorn
    
    config = uvicorn.Config(
        app=app,
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        loop="asyncio",
        limit_concurrency=settings.LIMIT_CONCURRENCY,
        backlog=settings.BACKLOG,
        timeout_keep_alive=settings.TIMEOUT_KEEP_ALIVE,
        log_level="info",
        access_log=True,
    )
    
    server = uvicorn.Server(config)
    
    setup_signal_handlers(server)
    
    print(f"\nServer starting at http://{settings.HOST}:{settings.PORT}")
    print("Press Ctrl+C to stop\n")
    
    # Run server
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        # Database optimization on shutdown
        try:
            import sqlite3
            conn = sqlite3.connect(settings.DB_PATH)
            conn.execute("VACUUM")
            conn.execute("PRAGMA optimize")
            conn.close()
            print("Database optimized (VACUUM)")
        except Exception as e:
            print(f"Warning: Could not optimize database: {e}")
        
        # Cleanup
        if hasattr(memory_system, 'cleanup'):
            memory_system.cleanup()
        if hasattr(llm_manager, 'cleanup'):
            llm_manager.cleanup()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()