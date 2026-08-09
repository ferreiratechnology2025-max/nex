"""Leitor de documentos para formatos TXT, MD, PDF, DOCX, JSON, CSV"""

import os
import json
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentReader:
    """Le e extrai texto de diferentes formatos de arquivo"""

    SUPPORTED_FORMATS = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".json": "application/json",
        ".csv": "text/csv",
    }

    async def read_file(self, file_path: str) -> str:
        """Le arquivo e retorna texto extraido"""
        ext = Path(file_path).suffix.lower()

        if ext in (".txt", ".md"):
            return self._read_text(file_path)
        elif ext == ".pdf":
            return self._read_pdf(file_path)
        elif ext == ".docx":
            return self._read_docx(file_path)
        elif ext == ".json":
            return self._read_json(file_path)
        elif ext == ".csv":
            return self._read_csv(file_path)
        else:
            raise ValueError(f"Formato nao suportado: {ext}")

    def _read_text(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _read_pdf(self, file_path: str) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                raise ImportError("Instale pypdf: pip install pypdf")

    def _read_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except ImportError:
            raise ImportError("Instale python-docx: pip install python-docx")

    def _read_json(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _read_csv(self, file_path: str) -> str:
        import csv
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = []
            for row in reader:
                rows.append(" | ".join(row))
            return "\n".join(rows)

    async def read_from_bytes(self, file_bytes: bytes, filename: str) -> str:
        """Le arquivo a partir de bytes (para upload)"""
        ext = Path(filename).suffix.lower()
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            tmp.write(file_bytes)
            tmp.close()
            return await self.read_file(tmp.name)
        finally:
            os.unlink(tmp.name)
