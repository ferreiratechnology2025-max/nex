"""Agente de Pesquisa - busca paralela na web, documentos e repositorios"""

import asyncio
import logging
import os
import re
from typing import Dict, List, Optional
from .base_agent import BaseAgent, AgentRole, AgentTask

logger = logging.getLogger(__name__)

_GITHUB_RE = re.compile(r"github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)")

_PRIORITY_FILES = frozenset({
    "README.md", "readme.md", "README", "app.py", "main.py",
    "streamlit_app.py", "index.py", "requirements.txt",
    "package.json", "setup.py", "pyproject.toml", "Makefile",
    "Dockerfile", "docker-compose.yml", "config.py",
    "config.toml", ".env.example", "compose.yaml",
})


class ResearcherAgent(BaseAgent):
    """Especialista em busca: web search + documentos + repositorios GitHub.

    Internamente paraleliza web search e busca documental via asyncio.gather()
    para reduzir latencia quando ambos os canais sao necessarios.
    Detecta automaticamente URLs do GitHub e le o codigo real via API.
    """

    def __init__(self, llm_manager, memory_manager, web_search_processor=None, document_manager=None):
        super().__init__(AgentRole.RESEARCHER, llm_manager, memory_manager)
        self.web_search = web_search_processor
        self.document_manager = document_manager

    # ------------------------------------------------------------------ #
    # Execute
    # ------------------------------------------------------------------ #

    async def execute(self, task: AgentTask, context: Dict) -> Dict:
        logger.info(f"Researcher executando: {task.description}")
        results = {"web_results": [], "document_results": [], "summary": ""}
        task_lower = task.description.lower()

        needs_web = any(w in task_lower for w in [
            "web", "internet", "pesquisar", "buscar", "noticia",
            "github.com", "repositorio", "repositório", "código", "codigo",
        ])
        needs_doc = any(w in task_lower for w in ["documento", "arquivo", "memoria", "doc"])

        if needs_web and needs_doc:
            web_coro = self._search_web(task.description)
            doc_coro = self._search_documents(task.description)
            web_out, doc_out = await asyncio.gather(web_coro, doc_coro, return_exceptions=True)
            results["web_results"] = web_out if not isinstance(web_out, Exception) else [{"error": str(web_out)}]
            results["document_results"] = doc_out if not isinstance(doc_out, Exception) else []
        else:
            if needs_web:
                results["web_results"] = await self._search_web(task.description)
            if needs_doc:
                results["document_results"] = await self._search_documents(task.description)

        results["summary"] = await self._summarize_findings(results)
        task.status = "completed"
        task.result = results
        return results

    # ------------------------------------------------------------------ #
    # Web search (com interceptacao de GitHub)
    # ------------------------------------------------------------------ #

    async def _search_web(self, query: str) -> List[Dict]:
        gh = self._parse_github_url(query)
        if gh:
            return await self._fetch_github_repo(gh["owner"], gh["repo"])

        if not self.web_search:
            return [{"error": "Web search nao disponivel"}]
        try:
            search_results = await self.web_search.search_and_read(query, max_pages=3)
            return [{"source": "web", "query": query, "results": search_results}]
        except Exception as e:
            logger.error(f"Erro na busca web: {e}")
            return [{"error": str(e)}]

    # ------------------------------------------------------------------ #
    # GitHub
    # ------------------------------------------------------------------ #

    def _parse_github_url(self, text: str) -> Optional[dict]:
        m = _GITHUB_RE.search(text)
        if not m:
            return None
        return {"owner": m.group(1), "repo": m.group(2).rstrip("/")}

    async def _fetch_github_repo(self, owner: str, repo: str) -> List[Dict]:
        """Le repositorio com fallback: GitHub API → gitingest → busca web."""

        # Tentativa 1: GitHub API (com suporte opcional a GITHUB_TOKEN)
        result = await self._github_api_fetch(owner, repo)
        if result and "error" not in result[0]:
            return result

        logger.warning("GitHub API falhou, tentando gitingest.com...")

        # Tentativa 2: gitingest.com (texto plano do repositorio)
        result = await self._gitingest_fetch(owner, repo)
        if result and "error" not in result[0]:
            return result

        logger.warning("gitingest falhou, revertendo para busca web...")

        # Tentativa 3: busca web tradicional como ultimo recurso
        return await self._web_search_fallback(owner, repo)

    # ------------------------------------------------------------------ #
    # GitHub API
    # ------------------------------------------------------------------ #

    async def _github_api_fetch(self, owner: str, repo: str) -> Optional[List[Dict]]:
        try:
            import aiohttp
        except ImportError:
            return None

        headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        blocks = []

        try:
            async with aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as s:
                # Metadados do repo
                async with s.get(f"https://api.github.com/repos/{owner}/{repo}") as r:
                    if r.status == 403:
                        logger.warning(f"GitHub rate limit ({owner}/{repo})")
                        return None
                    if r.status != 200:
                        return None
                    d = await r.json()
                    blocks.append(f"# {d['full_name']}")
                    blocks.append(f"**Descricao:** {d.get('description', 'N/A')}")
                    blocks.append(f"**Linguagem:** {d.get('language', 'N/A')}  |  "
                                  f"**Stars:** {d['stargazers_count']}  |  "
                                  f"**Forks:** {d['forks_count']}")
                    blocks.append(f"**Topicos:** {', '.join(d.get('topics', [])) or 'N/A'}")
                    blocks.append("")

                # Listagem + conteudo dos arquivos
                async with s.get(f"https://api.github.com/repos/{owner}/{repo}/contents") as r:
                    if r.status != 200:
                        return None
                    contents = await r.json()
                    blocks.append("## Arquivos do repositorio")
                    for item in contents[:30]:
                        blocks.append(f"- {item['name']}  ({item['type']})")
                    blocks.append("")

                    for item in contents:
                        if item["type"] != "file" or item["name"] not in _PRIORITY_FILES:
                            continue
                        async with s.get(item["download_url"]) as fr:
                            if fr.status == 200:
                                text = await fr.text()
                                blocks.append(f"### {item['name']}")
                                blocks.append(f"```\n{text[:3000]}\n```")
                                blocks.append("")

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Excecao na API GitHub ({owner}/{repo}): {e}")
            return None
        except Exception as e:
            logger.warning(f"Erro inesperado na API GitHub: {e}")
            return None

        if not blocks:
            return None

        combined = "\n".join(blocks)
        return [{
            "source": "github",
            "query": f"github.com/{owner}/{repo}",
            "results": [{
                "title": f"github/{owner}/{repo}",
                "url": f"https://github.com/{owner}/{repo}",
                "content": combined[:8000],
            }],
        }]

    # ------------------------------------------------------------------ #
    # gitingest fallback
    # ------------------------------------------------------------------ #

    async def _gitingest_fetch(self, owner: str, repo: str) -> Optional[List[Dict]]:
        url = f"https://gitingest.com/{owner}/{repo}"
        try:
            import aiohttp
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as s:
                async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
                    if r.status != 200:
                        logger.warning(f"gitingest HTTP {r.status} para {owner}/{repo}")
                        return None
                    text = await r.text()
        except ImportError:
            return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"gitingest falhou ({owner}/{repo}): {e}")
            return None
        except Exception as e:
            logger.warning(f"gitingest erro inesperado: {e}")
            return None

        if not text or len(text.strip()) < 100:
            return None

        return [{
            "source": "github",
            "query": f"github.com/{owner}/{repo}",
            "results": [{
                "title": f"github/{owner}/{repo} (gitingest)",
                "url": url,
                "content": text[:8000],
            }],
        }]

    # ------------------------------------------------------------------ #
    # Web search fallback
    # ------------------------------------------------------------------ #

    async def _web_search_fallback(self, owner: str, repo: str) -> List[Dict]:
        query = f"github.com/{owner}/{repo}"
        if self.web_search:
            try:
                results = await self.web_search.search_and_read(query, max_pages=3)
                if results:
                    return [{"source": "web", "query": query, "results": results}]
            except Exception as e:
                logger.warning(f"Web search fallback falhou: {e}")

        return [{"error": f"Nao foi possivel acessar o repositorio {owner}/{repo}"}]

    # ------------------------------------------------------------------ #
    # Documentos
    # ------------------------------------------------------------------ #

    async def _search_documents(self, query: str) -> List[Dict]:
        if not self.document_manager:
            return []
        try:
            docs = await self.document_manager.list_documents()
            relevant = []
            for doc in docs[:5]:
                full = await self.document_manager.get_document(doc["id"])
                if full and getattr(full, "content", None):
                    prompt = f"Query: {query}\nDocumento: {doc.get('filename')}\nRelevante? Responda SIM ou NAO."
                    is_rel = await self._generate_safe(prompt)
                    if "SIM" in is_rel.upper():
                        relevant.append({
                            "id": doc["id"],
                            "filename": doc["filename"],
                            "content": full.content[:1000],
                        })
            return relevant
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Sumario
    # ------------------------------------------------------------------ #

    async def _summarize_findings(self, results: Dict) -> str:
        if not results.get("web_results") and not results.get("document_results"):
            return "Nenhum resultado encontrado."
        web_text = str(results.get("web_results", []))[:500]
        doc_text = str(results.get("document_results", []))[:500]
        text = f"Web: {web_text}\nDocs: {doc_text}"
        prompt = f"Resuma os achados de pesquisa em portugues (max 200 palavras):\n{text}"
        return await self._generate_safe(prompt)
