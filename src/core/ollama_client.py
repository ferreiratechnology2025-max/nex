import json
import aiohttp
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "ornith:latest"
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0
    temperature: float = 0.7
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    num_ctx: int = 4096
    num_batch: int = 512
    use_gpu: bool = True


class OllamaClient:
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._model_available = False

    async def _ensure_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _ensure_connection(self) -> bool:
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status != 200:
                    logger.error(f"Ollama not responding: {response.status}")
                    return False
                data = await response.json()
                models = [m["name"] for m in data.get("models", [])]
                if self.config.model in models:
                    self._model_available = True
                    logger.info(f"Model {self.config.model} found locally")
                    return True
                logger.info(f"Model {self.config.model} not found. Pulling...")
                return await self._pull_model()
        except aiohttp.ClientError as e:
            logger.error(f"Ollama connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Ollama unexpected error: {e}")
            return False

    async def _pull_model(self) -> bool:
        try:
            pull_timeout = aiohttp.ClientTimeout(total=300)
            async with self.session.post(
                f"{self.config.base_url}/api/pull",
                json={"name": self.config.model},
                timeout=pull_timeout,
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Pull failed: {error_text}")
                    return False
                async for line in response.content:
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode())
                        if "status" in data:
                            logger.info(f"Pull: {data['status']}")
                        if data.get("completed", False):
                            self._model_available = True
                            logger.info(f"Model {self.config.model} pulled successfully")
                            return True
                    except json.JSONDecodeError:
                        continue
                return False
        except asyncio.TimeoutError:
            logger.error("Pull timed out after 300s")
            return False
        except Exception as e:
            logger.error(f"Pull error: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {
                        "status": "healthy",
                        "models": models,
                        "has_target_model": self.config.model in models,
                        "model_available": self._model_available,
                        "url": self.config.base_url,
                    }
                return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = True,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if not self._model_available:
            if not await self._ensure_connection():
                yield "[ERROR] Ollama unavailable. Check if the service is running."
                return
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        temp = temperature if temperature is not None else self.config.temperature
        max_tok = max_tokens or self.config.num_ctx
        payload = {
            "model": self.config.model,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "temperature": temp,
                "num_predict": max_tok,
                "top_k": self.config.top_k,
                "top_p": self.config.top_p,
                "repeat_penalty": self.config.repeat_penalty,
                "num_ctx": self.config.num_ctx,
                "num_batch": self.config.num_batch,
                **kwargs,
            },
        }
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.post(
                    f"{self.config.base_url}/api/generate", json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama error {response.status}: {error_text}")
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(self.config.retry_delay)
                            continue
                        yield f"[ERROR] Generation failed: {error_text}"
                        return
                    if stream:
                        async for token in self._parse_stream(response):
                            yield token
                    else:
                        data = await response.json()
                        yield data.get("response", "")
                    return
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                yield "[ERROR] Generation timed out"
                return
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} error: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                yield f"[ERROR] {str(e)}"
                return

    async def _parse_stream(self, response) -> AsyncGenerator[str, None]:
        buffer = ""
        async for chunk, _ in response.content.iter_chunks():
            if not chunk:
                continue
            buffer += chunk.decode()
            try:
                data = json.loads(buffer)
                if "response" in data:
                    yield data["response"]
                if data.get("done", False):
                    break
                buffer = ""
            except json.JSONDecodeError:
                continue

    async def generate_complete(self, prompt: str, **kwargs) -> str:
        result = ""
        async for token in self.generate(prompt=prompt, stream=True, **kwargs):
            result += token
        return result

    async def embeddings(self, text: str) -> List[float]:
        await self._ensure_session()
        if not self._model_available:
            if not await self._ensure_connection():
                logger.error("Ollama unavailable for embeddings")
                return []
        payload = {"model": self.config.model, "prompt": text}
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/embeddings", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    embedding = data.get("embedding", [])
                    if embedding:
                        logger.debug(f"Embedding generated: {len(embedding)} dimensions")
                    return embedding
                error_text = await response.text()
                logger.error(f"Embeddings error: {response.status} - {error_text}")
                return []
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []

    async def list_models(self) -> List[str]:
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
        return []

    async def get_model_info(self) -> Dict[str, Any]:
        await self._ensure_session()
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/show",
                json={"name": self.config.model},
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
        return {}

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        await self._ensure_session()
        await self._ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
