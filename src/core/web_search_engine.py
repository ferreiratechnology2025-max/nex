"""Mecanismo de busca independente usando DuckDuckGo (gratuito, sem API key)"""

import asyncio
import logging
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urlparse, parse_qs

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


class WebSearchEngine:
    """Busca na web usando DuckDuckGo HTML (gratuito, sem API key)"""

    DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Busca no DuckDuckGo e retorna resultados formatados."""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp nao disponivel, instalacao necessaria")
            return []

        params = {"q": query}
        headers = {"User-Agent": self.USER_AGENT}

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(
                    self.DUCKDUCKGO_HTML_URL,
                    data=params,
                    timeout=self.timeout
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"DuckDuckGo retornou HTTP {resp.status}")
                        return []
                    html = await resp.text()
                    return self._parse_results(html, max_results)
        except asyncio.TimeoutError:
            logger.error("Timeout ao buscar no DuckDuckGo")
            return []
        except Exception as e:
            logger.error(f"Erro na busca DuckDuckGo: {e}")
            return []

    def _parse_results(self, html: str, max_results: int) -> List[Dict]:
        """Parseia HTML de resultados do DuckDuckGo."""
        if not BS4_AVAILABLE:
            return self._parse_results_regex(html, max_results)
        return self._parse_results_bs4(html, max_results)

    def _parse_results_bs4(self, html: str, max_results: int) -> List[Dict]:
        """Parseia com BeautifulSoup."""
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for result in soup.select(".result")[:max_results]:
            title_elem = result.select_one(".result__title a")
            snippet_elem = result.select_one(".result__snippet")
            url_elem = result.select_one(".result__url")

            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            url = url_elem.get("href", "") if url_elem else ""
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            url = self._clean_ddg_url(url)

            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:500] if snippet else "",
                })

        return results

    def _parse_results_regex(self, html: str, max_results: int) -> List[Dict]:
        """Parseia com regex como fallback (sem BeautifulSoup)."""
        results = []
        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL
        )
        for match in pattern.finditer(html)[:max_results]:
            url = self._clean_ddg_url(match.group(1))
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:500] if snippet else "",
                })
        return results

    def _clean_ddg_url(self, url: str) -> str:
        """Extrai URL real do redirect do DuckDuckGo."""
        if "//duckduckgo.com/l/" in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            return params.get("uddg", [""])[0]
        return url


