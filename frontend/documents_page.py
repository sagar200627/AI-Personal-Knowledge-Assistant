"""
Documents Page UI Component.
Handles document uploads (PDF, DOCX, TXT), text extraction, recursive chunking, and ChromaDB vector indexing.
"""

from pathlib import Path
import streamlit as st
import config
from database.db_manager import DatabaseManager
from documents.doc_loader import DocumentLoader
from documents.doc_chunker import DocumentChunker
from retriever.retriever import VectorRetriever
from frontend.components import render_hero_banner, render_section_header
from utils.helpers import format_file_size, format_timestamp
from utils.logger import get_logger

logger = get_logger("DocumentsPage")


def render_documents_page(
    db: DatabaseManager,
    chunker: DocumentChunker,
    retriever: VectorRetriever,
) -> None:
    """Render Knowledge Documents management tab."""
    render_hero_banner(
        title="📚 Document Intelligence Center",
        subtitle="Upload and index PDFs and DOCX files into ChromaDB vector memory for semantic RAG search.",
    )

    # -------------------------------------------------------------------------
    # Document Upload Section
    # -------------------------------------------------------------------------
    render_section_header("Upload Knowledge Documents", "Upload PDF or DOCX files to extend your AI Knowledge Base.", icon="📤")

    uploaded_files = st.file_uploader(
        "Choose PDF, DOCX, or TXT files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        if st.button("🚀 Process & Index Documents", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.markdown(f"⏳ **Processing `{uploaded_file.name}`...**")

                # Save file to uploads folder
                save_path = config.UPLOADS_DIR / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    # 1. Load raw text
                    doc_data = DocumentLoader.load_file(save_path)

                    # 2. Chunk text recursively
                    chunks = chunker.chunk_text(
                        text=doc_data["content"],
                        source_name=doc_data["filename"],
                    )

                    # 3. Save DB record
                    doc_id = db.add_document(
                        filename=doc_data["filename"],
                        file_type=doc_data["file_type"],
                        file_size=doc_data["file_size"],
                        chunk_count=len(chunks),
                    )

                    # 4. Store Chunks in ChromaDB
                    retriever.add_document_chunks(
                        doc_id=doc_id,
                        filename=doc_data["filename"],
                        chunks=chunks,
                    )

                    st.success(f"✅ Successfully indexed `{uploaded_file.name}` into vector database ({len(chunks)} chunks).")
                except Exception as e:
                    logger.error(f"Error indexing {uploaded_file.name}: {e}")
                    st.error(f"❌ Failed to process `{uploaded_file.name}`: {str(e)}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.markdown("✨ **Processing complete!**")
            st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Indexed Documents List
    # -------------------------------------------------------------------------
    render_section_header("Indexed Knowledge Documents", "View and manage all active vector documents.", icon="📁")

    documents = db.get_documents()

    if not documents:
        st.info("ℹ️ No documents indexed yet. Upload a PDF or DOCX file above to get started!")
        return

    for doc in documents:
        with st.expander(f"📄 **{doc['filename']}**  ({format_file_size(doc['file_size'])}) - {doc['chunk_count']} chunks"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Format:** `{doc['file_type'].upper()}`")
                st.write(f"**Indexed At:** {format_timestamp(doc['created_at'])}")
            with col2:
                st.write(f"**Document ID:** `{doc['id']}`")
                st.write(f"**Total Vector Chunks:** `{doc['chunk_count']}`")
            with col3:
                if st.button("🗑️ Delete Document", key=f"del_{doc['id']}", use_container_width=True):
                    # Delete from ChromaDB & SQLite
                    retriever.delete_document_chunks(doc['id'])
                    db.delete_document(doc['id'])

                    # Optionally delete physical file
                    filepath = config.UPLOADS_DIR / doc['filename']
                    if filepath.exists():
                        filepath.unlink()

                    st.success(f"Deleted `{doc['filename']}`!")
                    st.rerun()
