"""
9R-2.1 — Document Chunker

Splits large documents (PDF / TXT / MD / EPUB) into semantic chunks.
Optimized for skillbook generation and long-document analysis.

Strategies:
  1. Markdown/TXT: Split by headers (## / ###) or blank lines
  2. PDF: Extract text, split by paragraph + size limit
  3. EPUB: Chapter-based splitting

Each chunk preserves context via sliding window overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DocumentChunk:
    """A single document chunk with metadata."""
    text: str
    index: int = 0
    source_path: str = ""
    chapter_title: str = ""
    page_range: tuple[int, int] = (0, 0)
    char_start: int = 0
    char_end: int = 0
    token_estimate: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def is_heading(self) -> bool:
        """Check if chunk looks like a heading/section title."""
        lines = self.text.strip().split("\n")
        if not lines:
            return False
        first = lines[0].strip()
        return (
            first.startswith("#")
            or first.startswith("第")
            or bool(re.match(r"^\d+\.[\s　]", first))
            or len(first) < 50 and len(lines) == 1
        )


class DocumentChunker:
    """Chunk large documents for parallel processing.

    Usage:
        chunker = DocumentChunker(max_chunk_size=8000, overlap=500)
        chunks = chunker.chunk_file("/path/to/book.pdf")
    """

    def __init__(
        self,
        max_chunk_size: int = 8000,   # characters per chunk
        overlap: int = 500,            # sliding window overlap
        min_chunk_size: int = 200,     # discard chunks smaller than this
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size

    def chunk_file(self, file_path: str) -> list[DocumentChunk]:
        """Read and chunk a document file. Supports pdf/txt/md/epub."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            text = self._read_pdf(file_path)
        elif suffix == ".epub":
            text = self._read_epub(file_path)
        elif suffix in (".txt", ".md", ".markdown"):
            text = path.read_text(encoding="utf-8")
        else:
            # Try as plain text
            text = path.read_text(encoding="utf-8")

        return self._chunk_text(text, source_path=file_path)

    def chunk_text(self, text: str, source_path: str = "") -> list[DocumentChunk]:
        """Chunk raw text string."""
        return self._chunk_text(text, source_path=source_path)

    # ── Internal ──

    def _chunk_text(self, text: str, source_path: str = "") -> list[DocumentChunk]:
        """Core chunking logic: header-aware with sliding window."""
        # Detect if markdown-style headers exist
        has_headers = bool(re.search(r"\n#{1,3}[\s　]", text))

        if has_headers:
            raw_chunks = self._split_by_headers(text)
        else:
            raw_chunks = self._split_by_size(text)

        # Filter small chunks and build DocumentChunk objects
        chunks: list[DocumentChunk] = []
        char_pos = 0
        for i, chunk_text in enumerate(raw_chunks):
            chunk_text = chunk_text.strip()
            if len(chunk_text) < self.min_chunk_size:
                continue

            # Extract heading if present
            chapter = ""
            lines = chunk_text.split("\n")
            if lines and lines[0].strip().startswith("#"):
                chapter = lines[0].strip().lstrip("#").strip()

            chunks.append(DocumentChunk(
                text=chunk_text,
                index=i,
                source_path=source_path,
                chapter_title=chapter,
                char_start=char_pos,
                char_end=char_pos + len(chunk_text),
                token_estimate=max(1, len(chunk_text) // 4),
            ))
            char_pos += len(chunk_text)

        return chunks

    def _split_by_headers(self, text: str) -> list[str]:
        """Split by markdown headers (## / ###)."""
        # Pattern: newline + # + space at start of line
        pattern = r"(?:\n|\r\n)(#{1,3}[\s　][^\n]+)"
        parts = re.split(pattern, text)

        chunks: list[str] = []
        current = ""
        for part in parts:
            if re.match(r"^#{1,3}[\s　]", part):
                if current.strip():
                    chunks.append(current.strip())
                current = part
            else:
                current += part

        if current.strip():
            chunks.append(current.strip())

        return self._merge_oversized(chunks)

    def _split_by_size(self, text: str) -> list[str]:
        """Split by paragraph boundaries with size limit."""
        # Split into paragraphs (blank line separated)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks: list[str] = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current) + len(para) > self.max_chunk_size and current:
                chunks.append(current.strip())
                # Sliding window: keep last overlap chars
                if self.overlap > 0 and len(current) > self.overlap:
                    current = current[-self.overlap:] + "\n\n" + para
                else:
                    current = para
            else:
                if current:
                    current += "\n\n"
                current += para

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _merge_oversized(self, chunks: list[str]) -> list[str]:
        """Split chunks that exceed max_chunk_size."""
        result: list[str] = []
        for chunk in chunks:
            if len(chunk) <= self.max_chunk_size:
                result.append(chunk)
                continue

            # Oversized chunk: split by paragraphs with overlap
            sub_chunks = self._split_by_size(chunk)
            result.extend(sub_chunks)
        return result

    @staticmethod
    def _read_pdf(file_path: str) -> str:
        """Extract text from PDF."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            texts = []
            for page in doc:
                texts.append(page.get_text())
            doc.close()
            return "\n".join(texts)
        except ImportError:
            raise ImportError(
                "PyMuPDF (fitz) required for PDF reading. "
                "Install: pip install PyMuPDF"
            )

    @staticmethod
    def _read_epub(file_path: str) -> str:
        """Extract text from EPUB."""
        try:
            from ebooklib import epub
            book = epub.read_epub(file_path)
            texts = []
            for item in book.get_items():
                if item.get_type() == 9:  # ebooklib.ITEM_DOCUMENT
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    texts.append(soup.get_text())
            return "\n".join(texts)
        except ImportError:
            raise ImportError(
                "ebooklib + beautifulsoup4 required for EPUB reading. "
                "Install: pip install EbookLib beautifulsoup4"
            )
