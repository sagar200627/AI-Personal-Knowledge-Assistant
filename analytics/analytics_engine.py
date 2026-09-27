"""
Analytics Engine module.
Generates metrics and pandas DataFrames for visualization in the Dashboard.
"""

from typing import Dict, Any, List
import pandas as pd
from database.db_manager import DatabaseManager
from retriever.retriever import VectorRetriever
from utils.logger import get_logger

logger = get_logger("AnalyticsEngine")


class AnalyticsEngine:
    """Computes usage statistics and data distributions for charts."""

    def __init__(self, db: DatabaseManager, retriever: VectorRetriever):
        self.db = db
        self.retriever = retriever

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Aggregate key KPI metrics."""
        db_stats = self.db.get_stats()
        vector_stats = self.retriever.get_stats()

        return {
            "total_sessions": db_stats["total_sessions"],
            "total_messages": db_stats["total_messages"],
            "total_documents": db_stats["total_documents"],
            "total_chunks": vector_stats["total_doc_chunks"],
            "total_memories": vector_stats["total_memories"],
        }

    def get_document_distribution(self) -> pd.DataFrame:
        """Get DataFrame of document breakdown by file type."""
        docs = self.db.get_documents()
        if not docs:
            return pd.DataFrame(columns=["file_type", "count"])

        df = pd.DataFrame(docs)
        type_counts = df["file_type"].value_counts().reset_index()
        type_counts.columns = ["file_type", "count"]
        return type_counts

    def get_session_message_counts(self) -> pd.DataFrame:
        """Get DataFrame of message count per session."""
        sessions = self.db.get_sessions()
        if not sessions:
            return pd.DataFrame(columns=["session_title", "message_count"])

        data = []
        for s in sessions:
            msgs = self.db.get_messages(s["id"])
            data.append({"session_title": s["title"], "message_count": len(msgs)})

        return pd.DataFrame(data)

    def get_memory_distribution(self) -> pd.DataFrame:
        """Get DataFrame of memories by type."""
        memories = self.db.get_memories_meta()
        if not memories:
            return pd.DataFrame(columns=["memory_type", "count"])

        df = pd.DataFrame(memories)
        type_counts = df["memory_type"].value_counts().reset_index()
        type_counts.columns = ["memory_type", "count"]
        return type_counts
