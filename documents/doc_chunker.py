"""
Document Chunker module.
Performs sliding window recursive text splitting into overlapping semantic chunks.
Built cleanly from scratch without third-party agent frameworks.
"""

from typing import List, Dict, Any
import config
from utils.logger import get_logger

logger = get_logger("DocChunker")


class DocumentChunker:
    """Splits text documents into manageable semantic chunks with overlap."""

    def __init__(
        self,
        chunk_size: int = config.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = config.DEFAULT_CHUNK_OVERLAP,
    ):
        """Initialize chunker with size and overlap.

        Args:
            chunk_size (int): Max character length per chunk.
            chunk_overlap (int): Overlap character count between adjacent chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    def chunk_text(self, text: str, source_name: str = "") -> List[Dict[str, Any]]:
        """Splits raw text into a list of chunk dictionaries.

        Args:
            text (str): Source text string.
            source_name (str): Document source identifier.

        Returns:
            List[Dict[str, Any]]: Array of chunk dicts containing chunk index, text, metadata.
        """
        if not text or not text.strip():
            return []

        raw_chunks = self._split_text_recursively(text, self.separators)

        # Build chunks with overlap and indices
        chunks = []
        for idx, chunk_str in enumerate(raw_chunks):
            if chunk_str.strip():
                chunks.append(
                    {
                        "chunk_index": idx,
                        "source": source_name,
                        "content": chunk_str.strip(),
                        "char_count": len(chunk_str.strip()),
                    }
                )

        logger.info(
            f"Chunked text from '{source_name}' ({len(text)} chars) into {len(chunks)} chunks "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})."
        )
        return chunks

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        """Recursive internal splitter strategy."""
        final_chunks = []
        if len(text) <= self.chunk_size or not separators:
            return [text]

        separator = separators[0]
        new_separators = separators[1:]

        splits = text.split(separator) if separator else list(text)

        current_chunk = []
        current_length = 0

        for split in splits:
            split_len = len(split) + len(separator)

            if current_length + split_len > self.chunk_size:
                if current_chunk:
                    joined = separator.join(current_chunk)
                    if len(joined) > self.chunk_size:
                        # Sub-split larger segment
                        final_chunks.extend(self._split_text_recursively(joined, new_separators))
                    else:
                        final_chunks.append(joined)

                    # Retain overlap from end of current_chunk
                    overlap_size = 0
                    overlap_items = []
                    for item in reversed(current_chunk):
                        if overlap_size + len(item) <= self.chunk_overlap:
                            overlap_items.insert(0, item)
                            overlap_size += len(item)
                        else:
                            break
                    current_chunk = overlap_items
                    current_length = overlap_size

            current_chunk.append(split)
            current_length += split_len

        if current_chunk:
            joined = separator.join(current_chunk)
            if len(joined) > self.chunk_size:
                final_chunks.extend(self._split_text_recursively(joined, new_separators))
            else:
                final_chunks.append(joined)

        return [c for c in final_chunks if c.strip()]
