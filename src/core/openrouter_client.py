"""Cliente wrapper para API OpenRouter com suporte a modelos free"""

import logging
import os
from typing import Optional, Dict, Any, List, AsyncGenerator
import json

logger = logging.getLogger(__name__)

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    logger.warning("httpx não instalado. OpenRouterClient usará requests (síncrono).")
    import requests


class OpenRouterClient:
    """Cliente assíncrono para OpenRouter API"""

    def __init__(self, api_key: str = "", model: str = "openrouter/owl-alpha",
                 fallback_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"):
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model
        self.base_url = "https://openrouter.ai/api/v1"
        self._available = None

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(self, messages: List[Dict], model: str,
                       temperature: float = 0.7, max_tokens: int = 2048,
                       stream: bool = False) -> Dict:
        return {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def chat_completion(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict:
        """Chat completion via OpenRouter com fallback de modelo"""
        result = await self._try_model(self.model, messages, temperature, max_tokens, stream)
        if result and "error" not in result:
            return result

        logger.warning(f"Modelo primário {self.model} falhou, tentando fallback {self.fallback_model}")
        result = await self._try_model(self.fallback_model, messages, temperature, max_tokens, stream)
        if result:
            return result

        return {"error": "Todos os modelos OpenRouter falharam", "choices": []}

    async def chat_completion_stream(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Streaming via SSE do OpenRouter"""
        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages, self.model, temperature, max_tokens, stream=True)
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream("POST", url, headers=headers, json=payload) as response:
                        if response.status_code >= 400:
                            logger.warning(f"Streaming falhou ({response.status_code}), tentando fallback")
                            async for token in self._stream_fallback(messages, temperature, max_tokens):
                                yield token
                            return
                        async for line in response.aiter_lines():
                            token = self._parse_sse_line(line)
                            if token:
                                yield token
            else:
                async for token in self._stream_fallback(messages, temperature, max_tokens):
                    yield token
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            async for token in self._stream_fallback(messages, temperature, max_tokens):
                yield token

    async def _stream_fallback(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Fallback para stream via modelo secundário"""
        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages, self.fallback_model, temperature, max_tokens, stream=True)
        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code >= 400:
                        return
                    async for line in response.aiter_lines():
                        token = self._parse_sse_line(line)
                        if token:
                            yield token
        except Exception:
            pass

    def _parse_sse_line(self, line: str) -> Optional[str]:
        """Parseia linha SSE e retorna token de texto se houver"""
        if line.startswith("data: "):
            data = line[6:].strip()
            if data == "[DONE]":
                return None
            try:
                chunk = json.loads(data)
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    return delta.get("content", "")
            except json.JSONDecodeError:
                pass
        return None

    async def _try_model(self, model: str, messages: List[Dict],
                          temperature: float, max_tokens: int,
                          stream: bool) -> Optional[Dict]:
        url = f"{self.base_url}/chat/completions"
        payload = self._build_payload(messages, model, temperature, max_tokens, stream)

        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, headers=self._get_headers(), json=payload)
                    return self._handle_response(response, model)
            else:
                response = requests.post(url, headers=self._get_headers(), json=payload, timeout=60)
                return self._handle_response(response, model)
        except Exception as e:
            logger.error(f"Erro OpenRouter ({model}): {e}")
            return {"error": str(e), "model": model}

    def _handle_response(self, response, model: str) -> Dict:
        if response.status_code == 401:
            return {"error": "Authentication failed", "model": model}
        elif response.status_code == 402:
            return {"error": "Insufficient credits or model not free", "model": model}
        elif response.status_code == 429:
            return {"error": "Rate limited", "model": model}
        elif response.status_code >= 400:
            return {"error": f"API error {response.status_code}", "model": model}

        try:
            data = response.json()
            if "error" in data:
                return {"error": data["error"].get("message", str(data["error"])), "model": model}
            data["_model"] = model
            return data
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON response: {e}", "model": model}

    async def is_available(self) -> bool:
        """Verifica se OpenRouter está acessível (modelos free não precisam de key)"""
        if self._available is not None:
            return self._available

        try:
            url = f"{self.base_url}/models"
            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers=self._get_headers())
            else:
                response = requests.get(url, headers=self._get_headers(), timeout=10)

            self._available = response.status_code < 500
            return self._available
        except Exception as e:
            logger.warning(f"OpenRouter health check falhou: {e}")
            self._available = False
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Retorna status detalhado da API OpenRouter"""
        available = await self.is_available()
        result = {
            "available": available,
            "model": self.model,
            "fallback_model": self.fallback_model,
            "has_api_key": bool(self.api_key),
        }
        if not available:
            result["error"] = "OpenRouter API não acessível"
        return result

    def parse_response_content(self, response: Dict) -> str:
        """Extrai conteúdo de texto da resposta"""
        try:
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")
        except Exception:
            pass
        return ""
