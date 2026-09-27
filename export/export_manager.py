"""
Export Manager module.
Converts session chat histories to TXT or Markdown formats for export.
"""

from typing import List, Dict, Any
from datetime import datetime
from utils.helpers import format_timestamp


class ExportManager:
    """Formatter for exporting chat logs into standard text formats."""

    @staticmethod
    def export_to_txt(session_title: str, messages: List[Dict[str, Any]]) -> str:
        """Format session chat log into plain text format.

        Args:
            session_title (str): Title of the session.
            messages (List[Dict[str, Any]]): Messages array.

        Returns:
            str: Plain text chat transcript.
        """
        header = (
            "==================================================\n"
            f"CHAT TRANSCRIPT: {session_title}\n"
            f"Exported At: {format_timestamp(datetime.now())}\n"
            "==================================================\n\n"
        )

        body_lines = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            time_str = format_timestamp(msg.get("created_at"))
            content = msg.get("content", "")
            context = msg.get("context_used")

            body_lines.append(f"[{time_str}] {role}:")
            body_lines.append(content)
            if context:
                body_lines.append(f"\n[Context Used]:\n{context}")
            body_lines.append("\n" + "-" * 40 + "\n")

        return header + "\n".join(body_lines)

    @staticmethod
    def export_to_markdown(session_title: str, messages: List[Dict[str, Any]]) -> str:
        """Format session chat log into Markdown format.

        Args:
            session_title (str): Title of the session.
            messages (List[Dict[str, Any]]): Messages array.

        Returns:
            str: Markdown formatted chat transcript.
        """
        header = (
            f"# Chat Transcript: {session_title}\n\n"
            f"**Exported At:** `{format_timestamp(datetime.now())}`  \n"
            f"**Total Messages:** {len(messages)}\n\n"
            "---\n\n"
        )

        body_lines = []
        for msg in messages:
            role = msg.get("role", "user")
            icon = "👤" if role == "user" else "🤖"
            role_name = "User" if role == "user" else "Assistant"
            time_str = format_timestamp(msg.get("created_at"))
            content = msg.get("content", "")
            context = msg.get("context_used")

            body_lines.append(f"### {icon} {role_name} *({time_str})*\n")
            body_lines.append(content + "\n")

            if context:
                body_lines.append("> **Retrieved RAG Context:**\n>")
                context_quoted = "\n> ".join(context.splitlines())
                body_lines.append(f"> {context_quoted}\n")

            body_lines.append("---\n")

        return header + "\n".join(body_lines)
