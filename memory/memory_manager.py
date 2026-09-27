"""
Long-Term Memory Manager module.
Integrates SQLite metadata storage and ChromaDB semantic memory vector search.
"""

import uuid
import re
from typing import List, Dict, Any, Optional
from database.db_manager import DatabaseManager
from retriever.retriever import VectorRetriever
from utils.logger import get_logger

logger = get_logger("MemoryManager")


class MemoryManager:
    """Manages long-term personal facts and context memory for the AI Agent."""

    def __init__(self, db: DatabaseManager, retriever: VectorRetriever):
        self.db = db
        self.retriever = retriever

    def save_memory(self, content: str, memory_type: str = "user_fact") -> str:
        """Store a long-term memory fact in SQLite and ChromaDB.

        Args:
            content (str): Memory text (e.g. "User's favorite programming language is Python").
            memory_type (str): Type tag.

        Returns:
            str: Generated memory ID.
        """
        memory_id = str(uuid.uuid4())
        content_clean = content.strip()

        if not content_clean:
            return ""

        # Save to database
        self.db.add_memory_meta(memory_id=memory_id, content=content_clean, memory_type=memory_type)

        # Save to vector retriever
        self.retriever.add_memory(memory_id=memory_id, content=content_clean, memory_type=memory_type)

        logger.info(f"Saved new memory [{memory_id}]: '{content_clean}'")
        return memory_id

    def retrieve_relevant_memories(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find semantic memories relevant to user's current query.

        Args:
            query (str): User prompt.
            top_k (int): Number of top memories.

        Returns:
            List[Dict[str, Any]]: List of matching memory records.
        """
        return self.retriever.search_memories(query=query, top_k=top_k)

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Retrieve all stored long-term memories."""
        return self.db.get_memories_meta()

    def delete_memory(self, memory_id: str) -> None:
        """Delete memory from SQLite and ChromaDB."""
        self.db.delete_memory_meta(memory_id)
        self.retriever.delete_memory(memory_id)
        logger.info(f"Deleted memory {memory_id}")

    def auto_extract_and_save(self, user_input: str) -> Optional[str]:
        """Automatically detect personal facts in user messages and save to long-term memory.

        Args:
            user_input (str): User message.

        Returns:
            Optional[str]: Saved memory ID if extracted, else None.
        """
        patterns = [
            r"my name is ([A-Za-z0-9\s]+)",
            r"i am a ([A-Za-z0-9\s]+)",
            r"i work as ([A-Za-z0-9\s]+)",
            r"i live in ([A-Za-z0-9\s]+)",
            r"my favorite ([A-Za-z0-9\s]+) is ([A-Za-z0-9\s]+)",
            r"remember that ([A-Za-z0-9\s,.]+)",
            r"i prefer ([A-Za-z0-9\s]+)",
        ]

        text_lower = user_input.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                fact = f"User state: {user_input.strip()}"
                # Avoid duplicate exact memories
                existing = self.get_all_memories()
                if not any(m["content"].lower() == fact.lower() for m in existing):
                    return self.save_memory(fact, memory_type="auto_extracted")
        return None
