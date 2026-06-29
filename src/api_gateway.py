"""
API Gateway Otimizado - Nex.spec.md Seção 2.3
FastAPI + Rate Limiter + Streaming + WebSocket
"""

import os
import sys
import json
import asyncio
import re
import logging
from collections import defaultdict
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Configurar templates com caminho absoluto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# import metrics middleware
from src.metrics import MetricsMiddleware, get_metrics
from src.core.document_reader import DocumentReader

# Security constants
ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx', '.json', '.csv'}
BLOCKED_MIME_PATTERNS = [
    'application/x-msdownload',
    'application/x-dosexec',
    'application/x-executable',
    'application/x-sharedlib',
    'application/vnd.microsoft.portable-executable',
    'text/html',
    'application/x-javascript',
]

logger = logging.getLogger(__name__)


def validate_file_size(content: bytes, max_mb: int = 10):
    if len(content) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"Arquivo excede tamanho maximo de {max_mb}MB")


def validate_file_extension(filename: str):
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            f"Extensao nao permitida: {ext}. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


def sanitize_filename(filename: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', '_', filename)
    name = name.replace('..', '_').replace('/', '_').replace('\\', '_')
    return name[:100]


def validate_mime_type(content: bytes, filename: str):
    try:
        import magic
        mime = magic.from_buffer(content[:1024], mime=True)

        for pattern in BLOCKED_MIME_PATTERNS:
            if pattern in mime:
                raise HTTPException(400, f"Tipo de arquivo nao permitido: {mime}")

        ext = Path(filename).suffix.lower()
        expected = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/plain',
            '.json': 'application/json',
            '.csv': 'text/csv',
        }.get(ext)

        if expected and expected not in mime:
            logger.warning(f"MIME mismatch: extensao {ext}, conteudo {mime}")
    except ImportError:
        logger.warning("python-magic nao instalado, pulando validacao MIME")


async def validate_content_bomb(content: str):
    if not content:
        return
    if '\x00' in content:
        raise HTTPException(400, "Arquivo contem caracteres nulos")
    if len(content) > 50000:
        unique_ratio = len(set(content.lower())) / len(content)
        if unique_ratio < 0.05:
            raise HTTPException(400, "Conteudo parece ser bomba de repeticao")


class Query(BaseModel):
    text: str
    max_tokens: int = Field(2048, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    stream: bool = False
    use_memory: bool = True
    use_web_search: bool = False


class Memory(BaseModel):
    text: str
    importance: float = Field(1.0, ge=0.0, le=2.0)


class DocumentQuery(BaseModel):
    document_id: str
    question: str


class DocumentSummaryRequest(BaseModel):
    document_id: str


class OrchestrateRequest(BaseModel):
    objective: str


class RateLimiter:
    """Rate limiter assíncrono com janela deslizante de 60s"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def check(self, client_id: str):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            window_start = now - 60
            
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if req_time > window_start
            ]
            
            if len(self.requests[client_id]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429, 
                    detail="Rate limit exceeded. Please wait before making more requests."
                )
            
            self.requests[client_id].append(now)


# NOTE: RateLimiter instance is created in main.py via app.state


async def get_llm_manager(request: Request):
    """Retorna o LLM Manager via app.state"""
    return request.app.state.llm_manager


async def get_memory_system(request: Request):
    """Retorna o sistema de memória via app.state"""
    return request.app.state.memory_system


async def get_document_reader(request: Request):
    return request.app.state.document_reader


async def get_document_manager(request: Request):
    return request.app.state.document_manager


async def get_coordinator(request: Request):
    return request.app.state.coordinator


async def get_rate_limiter(request: Request):
    return request.app.state.rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    # Startup: warm up fallback backends (non-blocking)
    try:
        if hasattr(app.state, "llm_manager") and app.state.llm_manager:
            asyncio.create_task(app.state.llm_manager.preload_llama_cpp_if_needed())
    except Exception:
        pass
    yield
    if hasattr(app.state, 'llm_manager') and app.state.llm_manager:
        if hasattr(app.state.llm_manager, 'cleanup'):
            app.state.llm_manager.cleanup()


app = FastAPI(
    title="Nex Local AI Assistant",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Configurar static files após app ser definido
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def get_client_id(request: Request) -> str:
    """Extrai ID do cliente para rate limiting"""
    return request.client.host if request.client else "default"


def build_prompt(query_text: str, context: str = "") -> str:
    """Constrói prompt com ou sem contexto"""
    if context:
        return f"""<|im_start|>system
You are a helpful assistant with access to the memories below.
Use them to answer, but only if relevant.

Memories:
{context}
<|im_end|>
<|im_start|>user
{query_text}<|im_end|>
<|im_start|>assistant
"""
    else:
        return f"<|im_start|>user\n{query_text}\n<|im_end|>\n<|im_start|>assistant\n"


async def save_interaction(memory, query_text: str, response: str):
    """Salva interação em background (sem bloquear)"""
    try:
        await memory.salvar_memoria(
            f"User: {query_text}\nAssistant: {response}",
            importancia=0.8
        )
    except Exception as e:
        print(f"Background save error: {e}")


@app.post("/ask")
async def ask(
    query: Query,
    background_tasks: BackgroundTasks,
    request: Request
):
    """Endpoint principal de pergunta"""
    await (await get_rate_limiter(request)).check(get_client_id(request))

    context = ""
    memories = []
    if query.use_memory:
        try:
            memory = await get_memory_system(request)
            memories = await memory.buscar_contexto(query.text, k=3)
            if memories:
                context = "\n\n".join([m['texto'] for m in memories])
        except Exception as e:
            print(f"Memory error: {e}")

    prompt = build_prompt(query.text, context)

    try:
        llm = await get_llm_manager(request)
        from src.core.llm_manager import Request as LLMRequest

        llm_request = LLMRequest(
            prompt=prompt,
            max_tokens=query.max_tokens,
            temperature=query.temperature,
            stream=query.stream
        )

        if query.stream:
            async def stream_generator():
                full_response = ""
                async for token in llm._generate_stream(llm_request):
                    full_response += token
                    yield token

                if query.use_memory:
                    background_tasks.add_task(
                        save_interaction, await get_memory_system(request),
                        query.text, full_response
                    )

            stream_headers = {
                "X-Backend-Used": llm.backend.value,
                "X-Fallback-Triggered": "false",
                "X-Fallback-Chain": getattr(llm, "last_fallback_chain", "openrouter->llama_cpp->huggingface"),
            }
            return StreamingResponse(stream_generator(), media_type="text/plain", headers=stream_headers)
        else:
            response = await llm.generate(
                llm_request,
                use_web_search=query.use_web_search
            )

            if query.use_memory:
                background_tasks.add_task(
                    save_interaction, await get_memory_system(request),
                    query.text, response
                )

            backend_used = (llm.last_backend_used.value if getattr(llm, "last_backend_used", None) else llm.backend.value)
            fallback_triggered = bool(getattr(llm, "last_fallback_triggered", False))
            response_headers = {
                "X-Backend-Used": backend_used,
                "X-Fallback-Triggered": str(fallback_triggered).lower(),
                "X-Fallback-Chain": getattr(llm, "last_fallback_chain", "openrouter->llama_cpp->huggingface"),
            }
            
            return JSONResponse(
                content={
                    "response": response,
                    "context_used": len(memories) if query.use_memory and context else 0,
                    "backend": backend_used
                },
                headers=response_headers
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


@app.post("/remember")
async def remember(
    memory_data: Memory,
    request: Request
):
    """Salva memória explicitamente"""
    await (await get_rate_limiter(request)).check(get_client_id(request))
    
    try:
        memory = await get_memory_system(request)
        memory_id = await memory.salvar_memoria(
            memory_data.text,
            importancia=memory_data.importance
        )
        
        return {
            "status": "saved",
            "id": memory_id,
            "text": memory_data.text[:100]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory save error: {str(e)}")


@app.get("/health")
async def health(request: Request):
    """Health check com status de backends"""
    from src.config import get_settings
    from pathlib import Path
    
    settings = get_settings()
    model_name = "unknown"
    device = "unknown"
    memory_count = 0
    
    llama_available = False
    llama_loaded = False
    hf_available = False
    hf_loaded = False
    ollama_available = False
    ollama_ready = False
    ollama_model = settings.OLLAMA_MODEL
    
    try:
        llm = await get_llm_manager(request)
        if llm:
            model_name = llm.get_model_name()
            device = llm.get_device()
            ollama_client = getattr(llm, "ollama_client", None)
            ollama_available = ollama_client is not None
            ollama_ready = ollama_client is not None and ollama_client._model_available
            llama_available = bool(getattr(llm, "can_use_llama_cpp", lambda: False)())
            llama_loaded = bool(getattr(llm, "is_llama_cpp_ready", lambda: False)())
            hf_loaded = bool(getattr(llm, "is_huggingface_ready", lambda: False)())
            hf_available = hf_loaded or settings.USE_HUGGINGFACE
    except:
        pass
    
    try:
        memory = await get_memory_system(request)
        if memory:
            stats = memory.get_stats()
            memory_count = stats.get('total_memories', 0)
    except:
        pass
    
    openrouter_available = llm and getattr(llm, "_openrouter_client", None) is not None
    
    return {
        "status": "ok",
        "model": model_name,
        "device": device,
        "memory_count": memory_count,
        "backends": {
            "ollama": {
                "available": ollama_available,
                "model": ollama_model,
                "ready": ollama_ready,
            },
            "openrouter": {
                "available": openrouter_available,
                "model": settings.OPENROUTER_MODEL,
                "fallback_model": settings.OPENROUTER_FALLBACK_MODEL,
            },
            "llama_cpp": {
                "available": llama_available or llama_loaded,
                "model": Path(settings.LOCAL_MODEL_PATH).name if settings.LOCAL_MODEL_PATH else None,
                "loaded": llama_loaded,
                "fallback_ready": llama_available or llama_loaded
            },
            "huggingface": {
                "available": hf_available,
                "model": settings.MODEL_NAME,
                "loaded": hf_loaded,
                "fallback_ready": bool((llama_available or llama_loaded) or (settings.USE_HUGGINGFACE and hf_loaded)),
            }
        },
        "fallback_order": ["ollama", "openrouter", "llama_cpp", "huggingface"]
    }


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    summarize: bool = Form(False),
    request: Request = None,
):
    """Upload seguro de documento com validacoes"""
    if request is None:
        raise HTTPException(400, "Request object missing")
    await (await get_rate_limiter(request)).check(get_client_id(request))

    from src.config import get_settings
    settings = get_settings()
    max_mb = settings.MAX_UPLOAD_SIZE_MB
    max_chars = settings.MAX_CONTENT_CHARS

    # 1. Ler com limite de tamanho
    raw = await file.read()
    if len(raw) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"Arquivo excede tamanho maximo de {max_mb}MB")

    # 2. Validar tamanho
    validate_file_size(raw, max_mb)

    # 3. Sanitizar nome
    safe_name = sanitize_filename(file.filename or "upload")

    # 4. Validar extensao
    validate_file_extension(safe_name)

    # 5. Validar MIME real
    validate_mime_type(raw, safe_name)

    # 6. Extrair texto
    reader = await get_document_reader(request)
    try:
        text = await reader.read_from_bytes(raw, safe_name)
    except ImportError as e:
        return JSONResponse(400, content={"error": str(e), "fix": f"pip install {str(e).name}"})
    except Exception as e:
        raise HTTPException(400, f"Falha ao processar arquivo: {e}")

    # 7. Validar bomba de conteudo
    await validate_content_bomb(text)

    # 8. Truncar se necessario
    if len(text) > max_chars:
        logger.warning(f"Conteudo truncado: {len(text)} -> {max_chars}")
        text = text[:max_chars]

    # 9. Salvar
    doc_mgr = await get_document_manager(request)
    doc_id = await doc_mgr.save_document(filename=safe_name, content=text)

    logger.info(f"Upload: {safe_name} -> {doc_id} ({len(text)} chars)")

    result = {
        "status": "success",
        "document_id": doc_id,
        "filename": safe_name,
        "size_chars": len(text),
    }

    if summarize:
        llm = await get_llm_manager(request)
        summary = await doc_mgr.summarize_document(doc_id, llm)
        result["summary"] = summary

    return result


@app.post("/ask_about_document")
async def ask_about_document(query: DocumentQuery, request: Request):
    """Pergunta sobre um documento especifico"""
    await (await get_rate_limiter(request)).check(get_client_id(request))

    doc_mgr = await get_document_manager(request)
    doc = await doc_mgr.get_document(query.document_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")

    prompt = (
        f"Documento: {doc.filename}\n\n"
        f"Conteudo:\n{doc.content[:4000]}\n\n"
        f"Pergunta: {query.question}\n\n"
        f"Responda com base APENAS no conteudo do documento acima:"
    )

    llm = await get_llm_manager(request)
    from src.core.llm_manager import Request

    answer = await llm.generate(Request(prompt=prompt, max_tokens=512))

    return {
        "document_id": query.document_id,
        "document": doc.filename,
        "question": query.question,
        "answer": answer,
    }


@app.post("/summarize_document")
async def summarize_document(req: DocumentSummaryRequest, request: Request):
    """Gera resumo de um documento"""
    await (await get_rate_limiter(request)).check(get_client_id(request))

    llm = await get_llm_manager(request)
    doc_mgr = await get_document_manager(request)

    summary = await doc_mgr.summarize_document(req.document_id, llm)

    if summary == "Documento nao encontrado":
        raise HTTPException(status_code=404, detail=summary)

    return {"document_id": req.document_id, "summary": summary}


@app.get("/documents")
async def list_documents(request: Request):
    """Lista documentos carregados"""
    doc_mgr = await get_document_manager(request)
    docs = await doc_mgr.list_documents()
    return {"documents": docs, "total": len(docs)}


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, request: Request):
    """Remove documento"""
    doc_mgr = await get_document_manager(request)
    ok = await doc_mgr.delete_document(document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    return {"status": "deleted", "document_id": document_id}


@app.post("/orchestrate")
async def orchestrate_task(req: OrchestrateRequest, request: Request):
    """Executa tarefa complexa com multiplos agentes (SSE streaming).

    Retorna Server-Sent Events com o progresso de cada etapa:
      data: {"stage": "research", "status": "running", "detail": "..."}

    Evento final:
      data: {"stage": "complete", "status": "done", "result": {...}}

    Exemplos:
    - "Pesquise sobre inteligencia artificial, analise tendencias e gere um relatorio"
    - "Leia meus documentos sobre contratos e sugira melhorias"
    """
    coordinator = getattr(request.app.state, "coordinator", None)
    if not coordinator:
        raise HTTPException(503, "Orquestrador nao disponivel")

    logger.info(f"Orquestracao SSE: {req.objective}")

    async def event_generator():
        try:
            async for event in coordinator.execute_stream(req.objective):
                if await request.is_disconnected():
                    logger.info("Cliente desconectado, encerrando stream")
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Erro no stream de orquestracao: {e}")
            error_event = {"stage": "error", "status": "failed", "detail": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Interface web principal"""
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    return FileResponse(index_path)


# Import and include WebSocket routes
from src.ws_handler import router as ws_router
app.include_router(ws_router, prefix="/ws")


@app.get("/metrics")
async def metrics_endpoint():
    """Metrics endpoint"""
    return get_metrics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
