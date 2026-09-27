"""
AI Personal Knowledge Assistant - Main Streamlit Application Entry Point.
Production-ready AI Agent with Long-Term Memory, RAG, Document Intelligence, and Modern Dark UI.
"""

import streamlit as st
import config
from frontend.styles import inject_custom_css
from database.db_manager import DatabaseManager
from retriever.retriever import VectorRetriever
from documents.doc_chunker import DocumentChunker
from memory.memory_manager import MemoryManager
from llm.hf_client import HuggingFaceClient
from rag.rag_engine import RAGEngine

from frontend.chat_page import render_chat_page
from frontend.documents_page import render_documents_page
from frontend.analytics_page import render_analytics_page
from frontend.settings_page import render_settings_page
from utils.logger import get_logger

logger = get_logger("AppMain")

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Modern Glassmorphism CSS Theme
inject_custom_css()


# -----------------------------------------------------------------------------
# Service Singleton Initialization (Cached in Session State)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_services():
    """Instantiate core singleton services once per application lifecycle."""
    logger.info("Initializing application backend services...")
    db = DatabaseManager()
    retriever = VectorRetriever()
    chunker = DocumentChunker()
    memory_manager = MemoryManager(db=db, retriever=retriever)
    hf_client = HuggingFaceClient()
    rag_engine = RAGEngine(
        retriever=retriever,
        memory_manager=memory_manager,
        hf_client=hf_client,
    )
    return db, retriever, chunker, memory_manager, hf_client, rag_engine


db, retriever, chunker, memory_manager, hf_client, rag_engine = get_services()

# -----------------------------------------------------------------------------
# Sidebar Main Navigation
# -----------------------------------------------------------------------------
st.markdown("""
<style>

/* Chat input text */
.stChatInput textarea {
    color: #111827 !important;
    background-color: #f1f5f9 !important;
}

/* Placeholder text */
.stChatInput textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}

/* Chat input container */
.stChatInput {
    background-color: #f1f5f9 !important;
}

/* Text cursor */
.stChatInput textarea {
    caret-color: #111827 !important;
}

</style>
""", unsafe_allow_html=True)


navigation_tab = st.sidebar.radio(
    "Navigation",
    options=[
        "💬 AI Chat",
        "📚 Knowledge Documents",
        "📊 Analytics & Memory",
        "⚙️ Settings",
    ],
    index=0,
)

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# Page Router
# -----------------------------------------------------------------------------
try:
    if navigation_tab == "💬 AI Chat":
        render_chat_page(db=db, rag_engine=rag_engine)
    elif navigation_tab == "📚 Knowledge Documents":
        render_documents_page(db=db, chunker=chunker, retriever=retriever)
    elif navigation_tab == "📊 Analytics & Memory":
        render_analytics_page(db=db, retriever=retriever, memory_manager=memory_manager)
    elif navigation_tab == "⚙️ Settings":
        render_settings_page(hf_client=hf_client)
except Exception as e:
    logger.error(f"Application error on tab {navigation_tab}: {e}", exc_info=True)
    st.error(f"⚠️ An application error occurred: {str(e)}")
