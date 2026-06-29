"""
LLM Manager - Suporte multi-backend:
- OpenRouter (cloud, prioritário)
- HuggingFace (local)
- Llama.cpp (GGUF local)
"""

import os
import asyncio
import logging
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator, Any, Union
from dataclasses import dataclass
from enum import Enum
logger = logging.getLogger(__name__)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class BackendType(str, Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    LLAMA_CPP = "llama_cpp"


@dataclass
class Request:
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = False
    future: Optional[asyncio.Future] = None


class LLMManager:
    """Gerencia LLM com suporte a múltiplos backends"""

    def __init__(self, config: Optional[Dict[str, Any]] = None, memory_manager=None):
        self.config = config or {}
        self.memory_manager = memory_manager
        self.backend = self._detect_backend()
        self._local_llm = None
        self._openrouter_client = None
        self._hf_ready = False
        self.hf_model = None
        self.hf_tokenizer = None

        self.ollama_client = None
        if str(self.config.get("ollama_enabled", os.environ.get("OLLAMA_ENABLED", "false"))).lower() in ("true", "1", "yes"):
            self._init_ollama()

        # Generation metadata (for API headers / debugging)
        self.last_backend_used: Optional[BackendType] = None
        self.last_fallback_triggered: bool = False
        self.last_fallback_reason: Optional[str] = None
        self.last_fallback_chain: str = "ollama->openrouter->llama_cpp->huggingface"

        # Web search
        self.web_search_processor = None

        if self.backend == BackendType.OPENROUTER:
            self._init_openrouter()
        elif self.backend == BackendType.LLAMA_CPP:
            self._init_llama_cpp()
        else:
            self._init_huggingface()

        self._init_web_search()

    def _detect_backend(self) -> BackendType:
        """Detecta qual backend usar baseado na config"""
        model_path = self.config.get("LOCAL_MODEL_PATH", os.environ.get("LOCAL_MODEL_PATH", ""))
        
        if model_path and os.path.exists(model_path):
            logger.info("Backend detectado: Llama.cpp (GGUF)")
            return BackendType.LLAMA_CPP

        logger.info("Backend detectado: OpenRouter")
        return BackendType.OPENROUTER

    def _reset_last_generation_meta(self):
        self.last_backend_used = None
        self.last_fallback_triggered = False
        self.last_fallback_reason = None

    def _get_local_model_path(self) -> str:
        return self.config.get("LOCAL_MODEL_PATH", os.environ.get("LOCAL_MODEL_PATH", "")) or ""

    def _can_import_llama_cpp(self) -> bool:
        return importlib.util.find_spec("llama_cpp") is not None

    def can_use_llama_cpp(self) -> bool:
        """Condições mínimas para usar llama.cpp como fallback (arquivo + lib)."""
        model_path = self._get_local_model_path()
        return bool(model_path and Path(model_path).exists() and self._can_import_llama_cpp())

    def is_llama_cpp_ready(self) -> bool:
        """True se o modelo GGUF já está carregado em memória."""
        return self._local_llm is not None

    def is_huggingface_ready(self) -> bool:
        """True se o modelo HuggingFace já está carregado em memória."""
        return bool(getattr(self, "_hf_ready", False))

    def _record_fallback_metric(self, from_backend: str, to_backend: str, reason: str):
        try:
            from src.metrics import metrics
            metrics.record_fallback(from_backend, to_backend, reason=reason)
        except Exception:
            pass

    def _load_llama_cpp_model_for_fallback(self) -> bool:
        """Carrega o modelo GGUF para fallback sem alterar self.backend."""
        if self._local_llm is not None:
            return True

        model_path = self._get_local_model_path()
        if not model_path or not Path(model_path).exists():
            return False

        if not self._can_import_llama_cpp():
            return False

        from llama_cpp import Llama

        n_ctx = int(self.config.get("LLAMA_N_CTX", os.environ.get("LLAMA_N_CTX", "2048")))
        n_threads = int(self.config.get("LOCAL_MODEL_THREADS", os.environ.get("LOCAL_MODEL_THREADS", "4")))
        n_gpu_layers = int(self.config.get("LLAMA_N_GPU_LAYERS", os.environ.get("LLAMA_N_GPU_LAYERS", "0")))

        logger.info(
            f"Carregando modelo GGUF para fallback: {model_path} (n_ctx={n_ctx}, n_threads={n_threads}, n_gpu_layers={n_gpu_layers})"
        )

        self._local_llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers,
            use_mlock=True,
            verbose=False,
        )
        return True

    async def preload_llama_cpp_if_needed(self):
        """Pré-carrega o modelo local em background para fallback rápido."""
        if not self.can_use_llama_cpp() or self.is_llama_cpp_ready():
            return
        try:
            await asyncio.get_running_loop().run_in_executor(None, self._load_llama_cpp_model_for_fallback)
            if self.is_llama_cpp_ready():
                logger.info("Modelo local pré-carregado para fallback")
        except Exception as e:
            logger.warning(f"Pré-carregamento do modelo local falhou: {e}")

    def _init_ollama(self):
        try:
            from src.core.ollama_client import OllamaClient, OllamaConfig
        except ImportError:
            from core.ollama_client import OllamaClient, OllamaConfig
        try:
            self.ollama_client = OllamaClient(
                OllamaConfig(
                    base_url=self.config.get("OLLAMA_URL", os.environ.get("OLLAMA_URL", "http://localhost:11434")),
                    model=self.config.get("OLLAMA_MODEL", os.environ.get("OLLAMA_MODEL", "ornith:latest")),
                    timeout=int(self.config.get("OLLAMA_TIMEOUT", os.environ.get("OLLAMA_TIMEOUT", "120"))),
                    temperature=float(self.config.get("OLLAMA_TEMPERATURE", os.environ.get("OLLAMA_TEMPERATURE", "0.7"))),
                    top_k=int(self.config.get("OLLAMA_TOP_K", os.environ.get("OLLAMA_TOP_K", "40"))),
                    top_p=float(self.config.get("OLLAMA_TOP_P", os.environ.get("OLLAMA_TOP_P", "0.9"))),
                    repeat_penalty=float(self.config.get("OLLAMA_REPEAT_PENALTY", os.environ.get("OLLAMA_REPEAT_PENALTY", "1.1"))),
                    num_ctx=int(self.config.get("OLLAMA_NUM_CTX", os.environ.get("OLLAMA_NUM_CTX", "4096"))),
                    num_batch=int(self.config.get("OLLAMA_NUM_BATCH", os.environ.get("OLLAMA_NUM_BATCH", "512"))),
                    use_gpu=str(self.config.get("OLLAMA_USE_GPU", os.environ.get("OLLAMA_USE_GPU", "true"))).lower() in ("true", "1", "yes"),
                )
            )
            logger.info("Ollama client initialized")
        except Exception as e:
            logger.warning(f"Ollama initialization failed: {e}")
            self.ollama_client = None

    def _init_openrouter(self):
        """Inicializa cliente OpenRouter como backend primário"""
        from src.core.openrouter_client import OpenRouterClient

        api_key = self.config.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))
        model = self.config.get("OPENROUTER_MODEL", os.environ.get("OPENROUTER_MODEL", "openrouter/owl-alpha"))
        fallback_model = self.config.get("OPENROUTER_FALLBACK_MODEL", os.environ.get("OPENROUTER_FALLBACK_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"))

        self._openrouter_client = OpenRouterClient(
            api_key=api_key,
            model=model,
            fallback_model=fallback_model,
        )

        logger.info(f"OpenRouter backend configurado: {model} (fallback: {fallback_model})")

    def _init_llama_cpp(self):
        """Inicializa modelo GGUF via llama.cpp com otimizações para CPU"""
        try:
            from llama_cpp import Llama
            
            model_path = self.config.get("LOCAL_MODEL_PATH", os.environ.get("LOCAL_MODEL_PATH", ""))
            if not model_path or not os.path.exists(model_path):
                logger.warning(f"Modelo GGUF não encontrado: {model_path}. Usando HuggingFace.")
                self.backend = BackendType.HUGGINGFACE
                self._init_huggingface()
                return
            
            n_ctx = int(self.config.get("LLAMA_N_CTX", os.environ.get("LLAMA_N_CTX", "2048")))
            n_threads = int(self.config.get("LOCAL_MODEL_THREADS", os.environ.get("LOCAL_MODEL_THREADS", "4")))
            n_gpu_layers = int(self.config.get("LLAMA_N_GPU_LAYERS", os.environ.get("LLAMA_N_GPU_LAYERS", "0")))
            
            print(f"Carregando modelo GGUF: {model_path}")
            print(f"n_gpu_layers={n_gpu_layers}, n_ctx={n_ctx}, n_threads={n_threads}")
            
            self._local_llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                use_mlock=True,
                verbose=False
            )
            
            self._loaded = True
            print(f"TinyLlama carregado com sucesso")
            
        except ImportError:
            logger.warning("llama-cpp-python não instalado. Usando HuggingFace.")
            self.backend = BackendType.HUGGINGFACE
            self._init_huggingface()
        except FileNotFoundError:
            logger.error(f"Modelo GGUF não encontrado: {model_path}. Usando HuggingFace.")
            self.backend = BackendType.HUGGINGFACE
            self._init_huggingface()
        except Exception as e:
            err_str = str(e)
            if "GGML" in err_str or "magic" in err_str:
                logger.error(f"Arquivo GGUF corrompido ou formato inválido: {e}")
            else:
                logger.error(f"Erro ao carregar modelo GGUF: {e}")
            self.backend = BackendType.HUGGINGFACE
            self._init_huggingface()

    def _init_huggingface(self):
        """Inicializa modelo HuggingFace local com fallback entre modelos"""
        import torch
        import gc

        self._hf_ready = False
        self.hf_model = None
        self.hf_tokenizer = None

        model_chain = [
            self.config.get("HF_MODEL_NAME", os.environ.get("HF_MODEL_NAME", "microsoft/phi-2")),
            self.config.get("HF_FALLBACK_MODEL", os.environ.get("HF_FALLBACK_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")),
        ]

        for model_name in model_chain:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM

                logger.info(f"Carregando modelo HuggingFace: {model_name}")
                self.hf_tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
                self.hf_model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True,
                )

                if self.hf_tokenizer.pad_token is None:
                    self.hf_tokenizer.pad_token = self.hf_tokenizer.eos_token

                self._hf_ready = True
                logger.info(f"HuggingFace carregado: {model_name}")
                break

            except Exception as e:
                logger.warning(f"Falha ao carregar {model_name}: {e}")
                self.hf_model = None
                self.hf_tokenizer = None
                continue

        if not self._hf_ready:
            logger.error("Nenhum modelo HuggingFace pôde ser carregado")
            gc.collect()

    def _init_web_search(self):
        """Inicializa processador de web search."""
        try:
            from .web_search import WebSearchProcessor
            self.web_search_processor = WebSearchProcessor(memory_manager=self.memory_manager)
            logger.info("WebSearchProcessor inicializado (DuckDuckGo)")
        except Exception as e:
            logger.warning(f"WebSearchProcessor nao disponivel: {e}")

    def _extract_query(self, prompt: str) -> str:
        """Extrai a pergunta real do usuario do prompt formatado."""
        import re
        match = re.search(r"<\|im_start\|>user\n(.+?)<\|im_end\|>", prompt, re.DOTALL)
        if match:
            return match.group(1).strip()
        return prompt[:500]

    def _use_huggingface(self) -> bool:
        """Retorna se o backend HuggingFace esta habilitado."""
        return str(self.config.get("USE_HUGGINGFACE", os.environ.get("USE_HUGGINGFACE", "true"))).lower() in ("true", "1", "yes")

    async def _try_openrouter(self, request: Request, system_prompt: Optional[str], use_web_search: bool) -> Optional[str]:
        """Try generating via OpenRouter. Returns None on failure."""
        if self._openrouter_client is None:
            return None
        try:
            return await self._generate_openrouter(request, system_prompt, use_web_search)
        except Exception as e:
            logger.warning(f"OpenRouter falhou: {e}")
            return None

    async def _try_openrouter_stream(self, request: Request) -> Optional[AsyncGenerator[str, None]]:
        """Tenta streaming via OpenRouter. Retorna None se falhar."""
        if self._openrouter_client is None:
            return None
        try:
            return self._generate_stream_openrouter(request)
        except Exception as e:
            logger.warning(f"OpenRouter stream falhou: {e}")
            return None

    async def _try_llama_cpp(self, request: Request, system_prompt: Optional[str]) -> Optional[str]:
        """Try generating via llama.cpp (GGUF local). Returns None on failure."""
        if not self.can_use_llama_cpp():
            return None
        try:
            if self._local_llm is None:
                await asyncio.get_running_loop().run_in_executor(None, self._load_llama_cpp_model_for_fallback)
            if self._local_llm is not None:
                return self._generate_llama_cpp(request, system_prompt)
        except Exception as e:
            logger.warning(f"llama_cpp falhou: {e}")
        return None

    async def _try_llama_cpp_stream(self, request: Request) -> Optional[AsyncGenerator[str, None]]:
        """Tenta streaming via llama.cpp. Retorna None se falhar."""
        if not self.can_use_llama_cpp():
            return None
        try:
            if self._local_llm is None:
                await asyncio.get_running_loop().run_in_executor(None, self._load_llama_cpp_model_for_fallback)
            if self._local_llm is not None:
                return self._generate_stream_llama_cpp(request)
        except Exception as e:
            logger.warning(f"llama_cpp stream falhou: {e}")
        return None

    async def _try_huggingface(self, request: Request) -> Optional[str]:
        """Try generating via HuggingFace local. Returns None on failure."""
        if not self._use_huggingface():
            return None
        try:
            if not self.is_huggingface_ready():
                await asyncio.get_running_loop().run_in_executor(None, self._init_huggingface)
            if self.is_huggingface_ready():
                return await self._generate_huggingface(request)
        except Exception as e:
            logger.warning(f"HuggingFace falhou: {e}")
        return None

    async def _try_huggingface_stream(self, request: Request) -> Optional[AsyncGenerator[str, None]]:
        """Tenta streaming via HuggingFace. Retorna None se falhar."""
        if not self._use_huggingface():
            return None
        try:
            if not self.is_huggingface_ready():
                await asyncio.get_running_loop().run_in_executor(None, self._init_huggingface)
            if self.is_huggingface_ready():
                return self._generate_stream_huggingface(request)
        except Exception as e:
            logger.warning(f"HuggingFace stream falhou: {e}")
        return None

    async def _try_ollama(self, request: Request, system_prompt: Optional[str] = None, use_web_search: bool = False) -> Optional[str]:
        if self.ollama_client is None:
            return None
        try:
            await self.ollama_client._ensure_session()
            if not self.ollama_client._model_available:
                if not await self.ollama_client._ensure_connection():
                    return None
            result = await self.ollama_client.generate_complete(
                prompt=request.prompt,
                system_prompt=system_prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            if result.startswith("[ERROR]"):
                return None
            return result
        except Exception as e:
            logger.warning(f"Ollama failed: {e}")
            return None

    async def _try_ollama_stream(self, request: Request) -> Optional[AsyncGenerator[str, None]]:
        if self.ollama_client is None:
            return None
        try:
            await self.ollama_client._ensure_session()
            if not self.ollama_client._model_available:
                if not await self.ollama_client._ensure_connection():
                    return None
            return self.ollama_client.generate(
                prompt=request.prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
        except Exception as e:
            logger.warning(f"Ollama stream failed: {e}")
            return None

    async def _execute_with_fallback(
        self,
        request: Request,
        system_prompt: Optional[str] = None,
        use_web_search: bool = False,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None], None]:
        """Executa requisicao com fallback em cascata entre backends.

        Ordem de prioridade: OpenRouter -> llama_cpp (GGUF) -> HuggingFace.

        Para stream=False: retorna str ou None se todos falharem.
        Para stream=True: retorna AsyncGenerator ou None se todos falharem.
        """
        self._reset_last_generation_meta()

        backends = []
        if getattr(self, "ollama_client", None) is not None:
            backends.append((BackendType.OLLAMA, self._try_ollama, self._try_ollama_stream))
        backends.extend([
            (BackendType.OPENROUTER, self._try_openrouter, self._try_openrouter_stream),
            (BackendType.LLAMA_CPP, self._try_llama_cpp, self._try_llama_cpp_stream),
            (BackendType.HUGGINGFACE, self._try_huggingface, self._try_huggingface_stream),
        ])

        for i, (backend_type, sync_fn, stream_fn) in enumerate(backends):
            try:
                if stream:
                    result = await stream_fn(request)
                else:
                    result = await sync_fn(request, system_prompt, use_web_search)

                if result is not None:
                    self.last_backend_used = backend_type
                    return result

            except Exception as e:
                logger.warning(f"Backend {backend_type.value} exception: {e}")

            if i < len(backends) - 1:
                self.last_fallback_triggered = True
                self.last_fallback_reason = self.last_fallback_reason or f"{backend_type.value}_failed"
                self._record_fallback_metric(backend_type.value, backends[i + 1][0].value, "fallback")

        logger.error("Todos os backends falharam")
        self.last_backend_used = self.last_backend_used or self.backend
        return None

    async def generate(
        self,
        request: Request,
        system_prompt: Optional[str] = None,
        use_web_search: bool = False
    ) -> str:
        """Gera resposta com fallback em cascata: OpenRouter -> llama_cpp -> huggingface.

        Importante: nunca deixa a excecao escapar (evita 500 no FastAPI).
        """
        result = await self._execute_with_fallback(request, system_prompt, use_web_search, stream=False)
        if result is not None:
            return result
        return "Desculpe, todos os backends de IA estao indisponiveis no momento. Por favor, tente novamente mais tarde ou configure uma API key do OpenRouter."

    async def _generate_stream(self, request: Request) -> AsyncGenerator[str, None]:
        """Streaming com fallback em cascata (openrouter -> llama_cpp -> huggingface).

        Importante: nunca deixa exceptions escaparem para o FastAPI.
        """
        generator = await self._execute_with_fallback(request, stream=True)
        if generator is not None:
            async for token in generator:
                yield token
            return
        yield "Desculpe, todos os backends de IA estao indisponiveis no momento. Por favor, tente novamente mais tarde ou configure uma API key do OpenRouter."

    def _generate_llama_cpp(self, request: Request, system_prompt: Optional[str] = None) -> str:
        """Geracao via Llama.cpp (GGUF)"""
        try:
            system_msg = system_prompt or "You are a helpful AI assistant."
            prompt = self._format_chatml([{"role": "system", "content": system_msg}, {"role": "user", "content": request.prompt}])
            
            max_tokens = request.max_tokens or 256
            temperature = request.temperature or 0.7
            
            result = self._local_llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|user|>"]
            )
            
            response = result["choices"][0]["text"].strip()
            return self._strip_assistant(response)
            
        except Exception as e:
            logger.error(f"Erro na geracao Llama.cpp: {e}")
            raise

    def _format_chatml(self, messages: list) -> str:
        """Formata mensagens no formato ChatML"""
        formatted = ""
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted += f"<|im_start|>{role}\n{msg['content']}<|im_end|>\n"
        formatted += "<|im_start|>assistant\n"
        return formatted

    def _strip_assistant(self, text: str) -> str:
        """Remove tokens de marcacao da resposta"""
        if text.startswith("<|assistant|>"):
            text = text[len("<|assistant|>"):]
        if text.startswith("<|im_start|>assistant\n"):
            text = text[len("<|im_start|>assistant\n"):]
        if "<|im_end|>" in text:
            text = text.split("<|im_end|>")[0]
        return text.strip()

    async def _generate_openrouter(
        self,
        request: Request,
        system_prompt: Optional[str],
        use_web_search: bool
    ) -> str:
        """Geracao via OpenRouter com suporte a busca na web independente."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        prompt = request.prompt
        if use_web_search and self.web_search_processor is not None:
            try:
                query = self._extract_query(prompt)
                search_results = await self.web_search_processor.search_and_format(
                    query, max_results=5
                )
                if search_results:
                    prompt = (
                        f"[INFORMACOES DA WEB]\n{search_results}\n\n"
                        f"[PERGUNTA ORIGINAL]\n{prompt}"
                    )
                    logger.info(f"Resultados da web injetados no prompt: {query[:60]}...")
            except Exception as e:
                logger.warning(f"Web search falhou, continuando sem: {e}")

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._openrouter_client.chat_completion(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            content = self._openrouter_client.parse_response_content(response)

            if not content and "error" in response:
                raise Exception(response["error"])

            return content or ""

        except Exception as e:
            logger.error(f"Erro na geracao OpenRouter: {e}")
            raise

    async def _generate_huggingface(self, request: Request) -> str:
        """Geracao via HuggingFace local"""
        if not self._hf_ready or self.hf_model is None or self.hf_tokenizer is None:
            raise Exception("HuggingFace model not initialized")

        import torch

        max_length = int(self.config.get("HF_MAX_LENGTH", os.environ.get("HF_MAX_LENGTH", "512")))

        inputs = self.hf_tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
        )

        with torch.no_grad():
            outputs = self.hf_model.generate(
                inputs.input_ids,
                max_new_tokens=min(request.max_tokens or 256, 512),
                temperature=request.temperature if request.temperature > 0 else 1.0,
                do_sample=request.temperature > 0,
                pad_token_id=self.hf_tokenizer.pad_token_id,
                eos_token_id=self.hf_tokenizer.eos_token_id,
            )

        response = self.hf_tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )

        return response.strip() or "Sorry, could not generate a response."

    async def _generate_stream_openrouter(self, request: Request) -> AsyncGenerator[str, None]:
        """Streaming via OpenRouter SSE"""
        messages = []
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})

        try:
            async for token in self._openrouter_client.chat_completion_stream(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 256,
            ):
                if token:
                    yield token
        except Exception as e:
            logger.error(f"Erro no streaming OpenRouter: {e}")
            raise

    async def _generate_stream_huggingface(self, request: Request) -> AsyncGenerator[str, None]:
        """Streaming token por token (HuggingFace)"""
        if not self._hf_ready or self.hf_model is None or self.hf_tokenizer is None:
            raise Exception("HuggingFace model not initialized")

        import torch

        max_length = int(self.config.get("HF_MAX_LENGTH", os.environ.get("HF_MAX_LENGTH", "512")))

        inputs = self.hf_tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
        )

        for _ in range(min(request.max_tokens or 256, 512)):
            with torch.no_grad():
                outputs = self.hf_model.generate(
                    inputs.input_ids,
                    max_new_tokens=1,
                    temperature=request.temperature if request.temperature > 0 else 1.0,
                    do_sample=request.temperature > 0,
                    pad_token_id=self.hf_tokenizer.pad_token_id,
                    eos_token_id=self.hf_tokenizer.eos_token_id,
                )

            next_token = outputs[0, -1]
            token_str = self.hf_tokenizer.decode(next_token, skip_special_tokens=True)

            if token_str:
                yield token_str

            if next_token == self.hf_tokenizer.eos_token_id:
                break

            inputs.input_ids = torch.cat([inputs.input_ids, next_token.unsqueeze(0).unsqueeze(0)], dim=1)

    async def _generate_stream_llama_cpp(self, request: Request) -> AsyncGenerator[str, None]:
        """Streaming via Llama.cpp com executor + timeout configuravel"""
        import asyncio
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        timeout_seconds = int(self.config.get("LOCAL_MODEL_TIMEOUT", os.environ.get("LOCAL_MODEL_TIMEOUT", "120")))
        
        try:
            system_msg = "You are a helpful AI assistant."
            prompt = self._format_chatml([{"role": "system", "content": system_msg}, {"role": "user", "content": request.prompt}])
            
            loop = asyncio.get_event_loop()
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                def generate():
                    return self._local_llm(
                        prompt,
                        max_tokens=request.max_tokens or 512,
                        temperature=request.temperature or 0.7,
                        stream=True,
                        stop=["<|user|>"]
                    )
                
                result = await loop.run_in_executor(executor, generate)
                
                for chunk in result:
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        logger.error(
                            f"Timeout na inferencia local: {elapsed:.1f}s > {timeout_seconds}s",
                            extra={"timeout_seconds": timeout_seconds, "elapsed_seconds": round(elapsed, 1)}
                        )
                        raise asyncio.TimeoutError(f"Local model timeout after {timeout_seconds}s")
                    
                    if "choices" in chunk and chunk["choices"]:
                        text = chunk["choices"][0].get("text", "")
                        if text:
                            yield self._strip_assistant(text)
                        
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout na inferencia local: {timeout_seconds}s ({e})")
            raise
        except Exception as e:
            logger.error(f"Erro no streaming Llama.cpp: {e}")
            raise

    def is_loaded(self) -> bool:
        if self.backend == BackendType.OLLAMA:
            return self.ollama_client is not None and self.ollama_client._model_available
        if self.backend == BackendType.OPENROUTER:
            return self._openrouter_client is not None
        if self.backend == BackendType.LLAMA_CPP:
            return self._local_llm is not None
        return bool(self._hf_ready)

    def get_device(self) -> str:
        if self.backend == BackendType.OLLAMA:
            return "local (Ollama)"
        if self.backend == BackendType.OPENROUTER:
            return "cloud"
        if self.backend == BackendType.LLAMA_CPP:
            return "GPU (GGUF)"
        hf_model = getattr(self, 'hf_model', None)
        if hf_model and hasattr(hf_model, 'device'):
            return str(hf_model.device)
        return "unknown"

    def get_model_name(self) -> str:
        if self.backend == BackendType.OLLAMA:
            return self.config.get("OLLAMA_MODEL", os.environ.get("OLLAMA_MODEL", "ornith:latest"))
        if self.backend == BackendType.OPENROUTER:
            return self.config.get("OPENROUTER_MODEL", os.environ.get("OPENROUTER_MODEL", "openrouter/owl-alpha"))
        elif self.backend == BackendType.LLAMA_CPP:
            return os.path.basename(self.config.get("LOCAL_MODEL_PATH", "tinyllama.gguf"))
        return self.config.get("HF_MODEL_NAME", os.environ.get("HF_MODEL_NAME", "microsoft/phi-2"))

    def cleanup(self):
        if self.ollama_client is not None:
            try:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    asyncio.ensure_future(self.ollama_client.close())
                except RuntimeError:
                    pass
            except Exception:
                pass
        if self.backend == BackendType.HUGGINGFACE and hasattr(self, 'hf_model'):
            import torch
            import gc

            del self.hf_model
            if hasattr(self, 'hf_tokenizer'):
                del self.hf_tokenizer
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self._hf_ready = False
            print("Model cleanup completed")
