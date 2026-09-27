"""
Retriever & ChromaDB Vector Store Manager.
Manages document embeddings and semantic search using ChromaDB and Sentence Transformers.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
import config
from utils.logger import get_logger

logger = get_logger("VectorRetriever")


class VectorRetriever:
    """Manages ChromaDB vector store and semantic search retrieval."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize ChromaDB persistent client and embedding function."""
        path_str = str(db_path or config.CHROMA_DB_DIR)
        logger.info(f"Initializing ChromaDB client at: {path_str}")

        self.client = chromadb.PersistentClient(path=path_str)

        # Initialize Sentence Transformer Embedding Function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.EMBEDDING_MODEL_NAME
        )

        # Collections
        self.doc_collection = self.client.get_or_create_collection(
            name="document_chunks",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

        self.memory_collection = self.client.get_or_create_collection(
            name="user_memories",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    # -------------------------------------------------------------------------
    # Document Vector Operations
    # -------------------------------------------------------------------------
    def add_document_chunks(self, doc_id: str, filename: str, chunks: List[Dict[str, Any]]) -> int:
        """Add chunked text records into the document_chunks vector collection.

        Args:
            doc_id (str): Database document UUID.
            filename (str): Source file name.
            chunks (List[Dict[str, Any]]): List of chunk objects.

        Returns:
            int: Number of chunks added.
        """
        if not chunks:
            return 0

        ids = [f"{doc_id}_chunk_{c['chunk_index']}" for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [
            {
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ]

        self.doc_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Indexed {len(chunks)} vector chunks for document '{filename}' (ID: {doc_id}).")
        return len(chunks)

    def search_documents(self, query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """Perform semantic similarity search on document chunks.

        Args:
            query (str): Search prompt/question.
            top_k (int): Number of top matches to retrieve.

        Returns:
            List[Dict[str, Any]]: Retrieved match records.
        """
        if not query or not query.strip():
            return []

        try:
            results = self.doc_collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self.doc_collection.count())),
            )

            retrieved = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

                for doc_text, meta, dist in zip(docs, metas, distances):
                    similarity = round(1.0 - float(dist), 3) if dist <= 1.0 else round(1.0 / (1.0 + float(dist)), 3)
                    retrieved.append(
                        {
                            "content": doc_text,
                            "filename": meta.get("filename", "Unknown"),
                            "doc_id": meta.get("doc_id", ""),
                            "chunk_index": meta.get("chunk_index", 0),
                            "score": similarity,
                        }
                    )
            return retrieved
        except Exception as e:
            logger.error(f"Error querying document collection: {e}")
            return []

    def delete_document_chunks(self, doc_id: str) -> None:
        """Remove all chunks associated with a document ID from ChromaDB."""
        try:
            self.doc_collection.delete(where={"doc_id": doc_id})
            logger.info(f"Deleted vector chunks for document {doc_id}.")
        except Exception as e:
            logger.error(f"Failed to delete document vectors for {doc_id}: {e}")

    # -------------------------------------------------------------------------
    # Long-Term Memory Vector Operations
    # -------------------------------------------------------------------------
    def add_memory(self, memory_id: str, content: str, memory_type: str = "user_fact") -> None:
        """Store a long-term memory entry in the vector store."""
        self.memory_collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[{"memory_type": memory_type, "memory_id": memory_id}],
        )
        logger.info(f"Indexed memory record in ChromaDB: '{memory_id}'")

    def search_memories(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant user memories semantically."""
        if not query or self.memory_collection.count() == 0:
            return []

        try:
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=min(top_k, self.memory_collection.count()),
            )

            retrieved = []
            if results and results.get("documents") and results["documents"][0]:
                docs = results["documents"][0]
                metas = results["metadatas"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

                for text, meta, dist in zip(docs, metas, distances):
                    similarity = round(1.0 - float(dist), 3) if dist <= 1.0 else round(1.0 / (1.0 + float(dist)), 3)
                    retrieved.append(
                        {
                            "content": text,
                            "memory_id": meta.get("memory_id", ""),
                            "memory_type": meta.get("memory_type", "user_fact"),
                            "score": similarity,
                        }
                    )
            return retrieved
        except Exception as e:
            logger.error(f"Error querying memory collection: {e}")
            return []

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory record from vector store."""
        try:
            self.memory_collection.delete(ids=[memory_id])
            logger.info(f"Deleted vector memory {memory_id}.")
        except Exception as e:
            logger.error(f"Failed to delete memory vector {memory_id}: {e}")

    # -------------------------------------------------------------------------
    # Collection Stats
    # -------------------------------------------------------------------------
    def get_stats(self) -> Dict[str, int]:
        """Return total document chunk count and total memory count."""
        return {
            "total_doc_chunks": self.doc_collection.count(),
            "total_memories": self.memory_collection.count(),
        }
