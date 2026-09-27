"""
SQLite Database Manager for AI Personal Knowledge Assistant.
Manages persistent relational data: Sessions, Messages, Documents, and Memory Metadata.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import config
from utils.logger import get_logger

logger = get_logger("DB_Manager")


class DatabaseManager:
    """Manages SQLite database connections and schema operations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DB_PATH
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a database connection with row factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Creates tables if they do not exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Sessions table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Messages table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        context_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                    )
                """
                )

                # Documents metadata table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        chunk_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Memory metadata table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memory_metadata (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        memory_type TEXT DEFAULT 'user_fact',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    def create_session(self, title: str = "New Chat") -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now),
            )
            conn.commit()
        logger.info(f"Created chat session: {session_id} - '{title}'")
        return session_id

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve all chat sessions ordered by latest updated."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def rename_session(self, session_id: str, new_title: str) -> None:
        """Rename an existing session."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (new_title, now, session_id),
            )
            conn.commit()
        logger.info(f"Renamed session {session_id} to '{new_title}'")

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session and its associated messages."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
        logger.info(f"Deleted session {session_id}")

    # -------------------------------------------------------------------------
    # Message Management
    # -------------------------------------------------------------------------
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        context_used: Optional[str] = None,
    ) -> str:
        """Add a message to a session."""
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, context_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, role, content, context_used, now),
            )
            # Update session timestamp
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            conn.commit()
        return msg_id

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Fetch all messages for a specific session."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    # -------------------------------------------------------------------------
    # Document Metadata Management
    # -------------------------------------------------------------------------
    def add_document(
        self, filename: str, file_type: str, file_size: int, chunk_count: int
    ) -> str:
        """Register a document in the database."""
        doc_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, filename, file_type, file_size, chunk_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, filename, file_type, file_size, chunk_count, now),
            )
            conn.commit()
        logger.info(f"Registered document {filename} (ID: {doc_id})")
        return doc_id

    def get_documents(self) -> List[Dict[str, Any]]:
        """Retrieve all documents."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_document(self, doc_id: str) -> None:
        """Remove a document entry."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Memory Metadata Management
    # -------------------------------------------------------------------------
    def add_memory_meta(self, memory_id: str, content: str, memory_type: str = "user_fact") -> None:
        """Add metadata record for long-term memory."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memory_metadata (id, content, memory_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (memory_id, content, memory_type, now),
            )
            conn.commit()

    def get_memories_meta(self) -> List[Dict[str, Any]]:
        """Retrieve all memory records."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_metadata ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_memory_meta(self, memory_id: str) -> None:
        """Delete a memory record."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM memory_metadata WHERE id = ?", (memory_id,))
            conn.commit()

    # -------------------------------------------------------------------------
    # Analytics & Aggregates
    # -------------------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Aggregate application usage statistics."""
        with self.get_connection() as conn:
            total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
            total_documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            total_chunks = conn.execute("SELECT SUM(chunk_count) FROM documents").fetchone()[0] or 0
            total_memories = conn.execute("SELECT COUNT(*) FROM memory_metadata").fetchone()[0]

            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_memories": total_memories,
            }
