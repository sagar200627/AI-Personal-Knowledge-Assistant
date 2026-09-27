"""
Document Loader module.

Extracts raw text content from PDF, DOCX, and TXT files.
Uses PyMuPDF (fitz) for PDF files and python-docx for DOCX files.
"""

from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF
import docx  # python-docx

from utils.logger import get_logger
from utils.helpers import clean_text


logger = get_logger("DocLoader")


class DocumentLoader:
    """Loader for PDF, DOCX, and TXT documents."""

    @staticmethod
    def load_pdf(file_path: Path) -> str:
        """
        Extract text from a PDF file using PyMuPDF (fitz).

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted and cleaned text from the PDF.

        Raises:
            ValueError: If the PDF cannot be read or parsed.
        """

        text_parts = []
        doc = None

        try:
            file_path = Path(file_path)

            # Open PDF
            doc = fitz.open(file_path)

            # IMPORTANT:
            # Store page count BEFORE closing the document.
            page_count = len(doc)

            logger.info(
                f"Reading PDF '{file_path.name}' "
                f"with {page_count} pages."
            )

            # Extract text from every page
            for page_num in range(page_count):

                page = doc.load_page(page_num)

                page_text = page.get_text("text")

                if page_text and page_text.strip():
                    text_parts.append(page_text)

            # Combine extracted text
            full_text = clean_text(
                "\n\n".join(text_parts)
            )

            logger.info(
                f"Loaded PDF '{file_path.name}': "
                f"extracted {len(full_text)} characters "
                f"across {page_count} pages."
            )

            return full_text

        except Exception as e:

            logger.exception(
                f"Error reading PDF file {file_path.name}: {e}"
            )

            raise ValueError(
                f"Could not parse PDF file "
                f"{file_path.name}: {str(e)}"
            )

        finally:
            # Always close the PDF safely
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

    @staticmethod
    def load_docx(file_path: Path) -> str:
        """
        Extract text from a DOCX file.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            Extracted and cleaned text.

        Raises:
            ValueError: If the DOCX cannot be read.
        """

        try:
            file_path = Path(file_path)

            doc = docx.Document(file_path)

            paragraphs = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()

                if text:
                    paragraphs.append(text)

            full_text = clean_text(
                "\n\n".join(paragraphs)
            )

            logger.info(
                f"Loaded DOCX '{file_path.name}': "
                f"extracted {len(full_text)} characters."
            )

            return full_text

        except Exception as e:

            logger.exception(
                f"Error reading DOCX file {file_path.name}: {e}"
            )

            raise ValueError(
                f"Could not parse DOCX file "
                f"{file_path.name}: {str(e)}"
            )

    @staticmethod
    def load_txt(file_path: Path) -> str:
        """
        Extract text from a TXT file.

        Args:
            file_path: Path to the TXT file.

        Returns:
            Extracted and cleaned text.
        """

        try:
            file_path = Path(file_path)

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                text = file.read()

            full_text = clean_text(text)

            logger.info(
                f"Loaded TXT '{file_path.name}': "
                f"extracted {len(full_text)} characters."
            )

            return full_text

        except Exception as e:

            logger.exception(
                f"Error reading TXT file {file_path.name}: {e}"
            )

            raise ValueError(
                f"Could not read TXT file "
                f"{file_path.name}: {str(e)}"
            )

    @classmethod
    def load_file(cls, file_path: Path) -> Dict[str, Any]:
        """
        Load a document based on its file extension.

        Supported formats:
            - PDF
            - DOCX
            - TXT

        Args:
            file_path: Path to the document.

        Returns:
            Dictionary containing document metadata and content.

        Raises:
            ValueError: If the file format is unsupported or
                        the document cannot be parsed.
        """

        file_path = Path(file_path)

        if not file_path.exists():
            raise ValueError(
                f"File does not exist: {file_path}"
            )

        extension = file_path.suffix.lower()

        # Load based on file type
        if extension == ".pdf":

            text = cls.load_pdf(file_path)

        elif extension == ".docx":

            text = cls.load_docx(file_path)

        elif extension == ".txt":

            text = cls.load_txt(file_path)

        else:

            raise ValueError(
                f"Unsupported file format: '{extension}'. "
                f"Supported formats: .pdf, .docx, .txt"
            )

        # Check whether any text was extracted
        if not text.strip():

            raise ValueError(
                f"No readable text was found in "
                f"'{file_path.name}'. "
                f"The document may contain scanned images "
                f"rather than selectable text."
            )

        return {
            "filename": file_path.name,
            "file_type": extension.lstrip("."),
            "file_size": file_path.stat().st_size,
            "content": text,
        }