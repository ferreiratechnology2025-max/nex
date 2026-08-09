"""Gerenciador de documentos com armazenamento em memoria persistente"""

import uuid
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Document:
    id: str
    filename: str
    content: str
    summary: Optional[str] = None
    created_at: str = ""
    size_chars: int = 0


DOC_PREFIX = "[DOC:"


class DocumentManager:
    """Armazena documentos na memoria persistente e recupera por ID"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self._docs: Dict[str, Document] = {}

    async def save_document(self, filename: str, content: str) -> str:
        """Salva documento na memoria persistente e retorna ID."""
        doc_id = str(uuid.uuid4())[:8]
        doc = Document(
            id=doc_id,
            filename=filename,
            content=content[:10000],
            created_at=datetime.utcnow().isoformat(),
            size_chars=len(content),
        )
        self._docs[doc_id] = doc

        memory_text = (
            f"{DOC_PREFIX}{doc_id}]\n"
            f"Arquivo: {filename}\n"
            f"Data: {doc.created_at}\n"
            f"Tamanho: {doc.size_chars} chars\n\n"
            f"Conteudo:\n{content[:5000]}"
        )
        try:
            await self.memory_manager.salvar_memoria(memory_text, importancia=1.2)
        except Exception as e:
            logger.warning(f"Erro ao salvar documento na memoria: {e}")

        logger.info(f"Documento salvo: {filename} -> {doc_id} ({doc.size_chars} chars)")
        return doc_id

    async def get_document(self, doc_id: str) -> Optional[Document]:
        """Recupera documento por ID (do cache em memoria)."""
        return self._docs.get(doc_id)

    async def list_documents(self) -> List[Dict]:
        """Lista metadados de todos os documentos carregados."""
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "size_chars": d.size_chars,
                "has_summary": d.summary is not None,
                "created_at": d.created_at,
            }
            for d in self._docs.values()
        ]

    async def delete_document(self, doc_id: str) -> bool:
        """Remove documento do cache."""
        if doc_id in self._docs:
            del self._docs[doc_id]
            return True
        return False

    async def summarize_document(self, doc_id: str, llm_manager) -> str:
        """Gera resumo do documento usando o LLM configurado."""
        doc = self._docs.get(doc_id)
        if not doc:
            return "Documento nao encontrado"

        prompt = (
            f"Resuma o documento abaixo em ate 3 paragrafos concisos.\n\n"
            f"Titulo: {doc.filename}\n\n"
            f"Conteudo:\n{doc.content[:4000]}\n\n"
            f"Resumo:"
        )

        from .llm_manager import Request
        summary = await llm_manager.generate(Request(prompt=prompt, max_tokens=512))
        doc.summary = summary

        try:
            await self.memory_manager.salvar_memoria(
                f"Resumo do documento '{doc.filename}': {summary}",
                importancia=1.0,
            )
        except Exception as e:
            logger.warning(f"Erro ao salvar resumo na memoria: {e}")

        return summary
