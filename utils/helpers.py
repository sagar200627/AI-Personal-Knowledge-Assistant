"""
Helper utility functions for data formatting, file operations, and text processing.
"""

from datetime import datetime
from typing import Union
from pathlib import Path


def format_timestamp(ts: Union[str, float, datetime] = None) -> str:
    """Format timestamp into clean human readable string.

    Args:
        ts: Timestamp object, float epoch, or ISO string.

    Returns:
        str: Formatted timestamp.
    """
    if ts is None:
        dt = datetime.now()
    elif isinstance(ts, datetime):
        dt = ts
    elif isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts)
    elif isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            return ts
    else:
        dt = datetime.now()

    return dt.strftime("%b %d, %Y %I:%M %p")


def format_file_size(size_bytes: int) -> str:
    """Format file size bytes into readable KB/MB string.

    Args:
        size_bytes (int): File size in bytes.

    Returns:
        str: Formatted string (e.g. 1.5 MB).
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def clean_text(text: str) -> str:
    """Clean text by stripping excessive whitespaces and newlines.

    Args:
        text (str): Input text string.

    Returns:
        str: Normalized cleaned string.
    """
    if not text:
        return ""
    # Normalize multiple newlines and spaces
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def truncate_text(text: str, max_chars: int = 100) -> str:
    """Truncate text to max length with ellipsis.

    Args:
        text (str): Input text string.
        max_chars (int): Maximum length.

    Returns:
        str: Truncated string.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
