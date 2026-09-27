"""
Unit tests for DocumentChunker.
"""

import unittest
from documents.doc_chunker import DocumentChunker


class TestDocumentChunker(unittest.TestCase):
    """Test text chunker recursive splitting strategy."""

    def setUp(self):
        self.chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

    def test_chunking_small_text(self):
        text = "Short text."
        chunks = self.chunker.chunk_text(text, source_name="test.txt")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["content"], "Short text.")

    def test_chunking_large_text(self):
        text = "Paragraph one is here. " * 10 + "\n\n" + "Paragraph two is here. " * 10
        chunks = self.chunker.chunk_text(text, source_name="test_large.txt")
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(chunk["char_count"], 150)


if __name__ == "__main__":
    unittest.main()
