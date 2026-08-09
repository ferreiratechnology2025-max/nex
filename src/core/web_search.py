"""Web search - busca independente na web e leitura de paginas"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    site_name: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0


@dataclass
class PageContent:
    url: str
    title: str
    content: str
    content_length: int
    read_at: str


class WebSearchProcessor:
    """Processa busca na web e leitura de paginas.
    
    Usa DuckDuckGo para buscar (gratuito, sem API key) e aiohttp+BS4 para ler paginas.
    """

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from .web_search_engine import WebSearchEngine
            self._engine = WebSearchEngine()
        return self._engine

    async def search_and_read(self, query: str, max_pages: int = 3) -> List[Dict[str, Any]]:
        """Busca na web e retorna resultados estruturados."""
        logger.info(f"Buscando na web: {query}")
        engine = self._get_engine()

        raw_results = await engine.search(query, max_results=max_pages)

        if not raw_results:
            logger.info(f"Nenhum resultado encontrado para: {query}")
            return []

        results = []
        for r in raw_results:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("snippet", ""),
                "site_name": self._extract_domain(r.get("url", "")),
            })

        if self.memory_manager:
            await self._save_search_to_memory(results, query)

        return results

    async def search_and_format(self, query: str, max_results: int = 5) -> str:
        """Busca na web e retorna string formatada para injecao no prompt."""
        engine = self._get_engine()
        raw_results = await engine.search(query, max_results=max_results)

        if not raw_results:
            return f"Nao encontrei resultados na web para: {query}"

        lines = [f"## Resultados da busca: {query}", ""]
        for i, r in enumerate(raw_results, 1):
            lines.append(f"{i}. **{r.get('title', 'Sem titulo')}**")
            lines.append(f"   URL: {r.get('url', '')}")
            lines.append(f"   {r.get('snippet', '')}")
            lines.append("")

        if self.memory_manager:
            search_results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("snippet", ""),
                    "site_name": self._extract_domain(r.get("url", "")),
                }
                for r in raw_results
            ]
            await self._save_search_to_memory(search_results, query)

        return "\n".join(lines).strip()

    def parse_search_response(self, response: Dict) -> List[SearchResult]:
        """Extrai resultados de resposta de API (formato dict)"""
        results = []
        try:
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                if content:
                    result = SearchResult(
                        title="Resultado da busca",
                        url="",
                        content=content[:500],
                        site_name="web",
                    )
                    results.append(result)
            logger.info(f"Extraidos {len(results)} resultados")
        except Exception as e:
            logger.error(f"Erro ao parsear resposta: {e}")
        return results

    async def save_to_memory(self, search_results: List[SearchResult], query: str) -> int:
        """Salva resultados de busca no sistema de memoria persistente"""
        if not self.memory_manager:
            logger.warning("Memory manager nao disponivel, nao salvando buscas")
            return 0

        saved_count = 0
        for result in search_results:
            memory_text = f"""
Busca: {query}
Fonte: {result.site_name} ({result.url})
Titulo: {result.title}
Conteudo: {result.content[:1000]}
Data: {result.published_date or 'Nao informada'}
"""
            try:
                await self.memory_manager.salvar_memoria(
                    memory_text.strip(),
                    importancia=0.8
                )
                saved_count += 1
            except Exception as e:
                logger.error(f"Erro ao salvar resultado na memoria: {e}")

        logger.info(f"{saved_count} resultados salvos na memoria")
        return saved_count

    async def _save_search_to_memory(self, results: List[Dict], query: str):
        """Salva resultados de busca como memorias."""
        try:
            memory_text = f"Busca na web: {query}\n"
            for r in results[:3]:
                memory_text += f"- {r.get('title', '')}: {r.get('content', '')[:200]}\n"
            await self.memory_manager.salvar_memoria(memory_text.strip(), importancia=0.6)
        except Exception as e:
            logger.warning(f"Erro ao salvar busca na memoria: {e}")

    def format_for_context(self, search_results: List[SearchResult], max_results: int = 3) -> str:
        """Formata resultados para contexto do LLM"""
        if not search_results:
            return "Nenhum resultado encontrado."
        context = "## Resultados da busca na web:\n\n"
        for i, result in enumerate(search_results[:max_results]):
            context += f"""### Resultado {i+1}: {result.title}
- **Fonte:** {result.site_name}
- **URL:** {result.url}
- **Data:** {result.published_date or 'Nao disponivel'}
- **Conteudo:** {result.content[:500]}...

"""
        return context

    async def read_full_page(self, url: str, save_to_memory: bool = True) -> Dict[str, Any]:
        """Le uma pagina web completa via HTTP"""
        logger.info(f"Lendo pagina: {url}")

        content = await self._read_via_requests(url)

        if not content:
            logger.error(f"Falha ao ler pagina: {url}")
            return {"error": "Nao foi possivel ler a pagina", "url": url}

        result = {
            "url": url,
            "title": content.get("title", "Sem titulo"),
            "content": content.get("content", ""),
            "content_length": len(content.get("content", "")),
            "read_at": datetime.now(timezone.utc).isoformat()
        }

        if save_to_memory and self.memory_manager and result["content"]:
            await self._save_page_to_memory(result)

        return result

    async def _read_via_requests(self, url: str) -> Optional[Dict[str, str]]:
        """Leitura de pagina via aiohttp + BeautifulSoup"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp nao disponivel")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} para {url}")
                        return None

                    html = await response.text()

                    if BS4_AVAILABLE:
                        soup = BeautifulSoup(html, 'html.parser')
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                        title = soup.find('title')
                        title_text = title.get_text().strip() if title else "Sem titulo"
                        text_parts = []
                        for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section']):
                            text = p.get_text().strip()
                            if text:
                                text_parts.append(text)
                        content = ' '.join(text_parts)
                    else:
                        import re
                        title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                        title_text = title.group(1).strip() if title else "Sem titulo"
                        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                        text = re.sub(r'<[^>]+>', ' ', text)
                        text = re.sub(r'\s+', ' ', text)
                        content = text.strip()

                    if len(content) > 10000:
                        content = content[:10000] + "..."

                    return {"title": title_text, "content": content}

        except Exception as e:
            logger.error(f"Erro na leitura HTTP: {e}")
            return None

    async def _save_page_to_memory(self, page_data: Dict[str, Any]) -> bool:
        """Salva pagina lida na memoria persistente"""
        try:
            memory_text = f"""
Pagina Web: {page_data['title']}
URL: {page_data['url']}
Lida em: {page_data['read_at']}

Conteudo:
{page_data['content'][:3000]}
"""
            await self.memory_manager.salvar_memoria(memory_text.strip(), importancia=1.2)
            logger.info(f"Pagina salva na memoria: {page_data['title'][:50]}...")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar pagina: {e}")
            return False

    def _extract_domain(self, url: str) -> str:
        """Extrai dominio de uma URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except Exception:
            return url
