"""
Analytics Page UI Component.
Renders KPI metrics, Plotly interactive data visualizations, and Long-Term Memory Manager.
"""

import streamlit as st
import plotly.express as px  # type: ignore # pyright: ignore[reportMissingImports]
from database.db_manager import DatabaseManager
from retriever.retriever import VectorRetriever
from memory.memory_manager import MemoryManager
from analytics.analytics_engine import AnalyticsEngine
from frontend.components import render_hero_banner, render_metric_card, render_section_header
from utils.helpers import format_timestamp


def render_analytics_page(
    db: DatabaseManager,
    retriever: VectorRetriever,
    memory_manager: MemoryManager,
) -> None:
    """Render Analytics Dashboard and Long-Term Memory Inspector."""
    render_hero_banner(
        title="📊 Knowledge & Analytics Dashboard",
        subtitle="Real-time usage metrics, document distribution, and active memory inspection.",
    )

    engine = AnalyticsEngine(db=db, retriever=retriever)
    stats = engine.get_summary_metrics()

    # -------------------------------------------------------------------------
    # Top KPI Metrics Row
    # -------------------------------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("Sessions", str(stats["total_sessions"]), icon="💬", subtext="Active chats")
    with col2:
        render_metric_card("Messages", str(stats["total_messages"]), icon="✉️", subtext="Total exchanged")
    with col3:
        render_metric_card("Documents", str(stats["total_documents"]), icon="📄", subtext="Indexed files")
    with col4:
        render_metric_card("Vector Chunks", str(stats["total_chunks"]), icon="🧩", subtext="ChromaDB chunks")
    with col5:
        render_metric_card("Memories", str(stats["total_memories"]), icon="🧠", subtext="Long-term facts")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Data Visualization Charts Row
    # -------------------------------------------------------------------------
    render_section_header("System Visualizations", "Explore conversation volume and knowledge distribution.", icon="📈")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 💬 Messages per Chat Session")
        session_df = engine.get_session_message_counts()
        if not session_df.empty:
            fig_sessions = px.bar(
                session_df,
                x="session_title",
                y="message_count",
                labels={"session_title": "Session", "message_count": "Messages"},
                color="message_count",
                color_continuous_scale="Purples",
                template="plotly_dark",
            )
            fig_sessions.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_sessions, use_container_width=True)
        else:
            st.info("No chat history available for plotting.")

    with chart_col2:
        st.markdown("#### 📁 Document Format Breakdown")
        doc_df = engine.get_document_distribution()
        if not doc_df.empty:
            fig_docs = px.pie(
                doc_df,
                names="file_type",
                values="count",
                hole=0.4,
                color_discrete_sequence=["#818cf8", "#c084fc", "#38bdf8"],
                template="plotly_dark",
            )
            fig_docs.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_docs, use_container_width=True)
        else:
            st.info("No documents uploaded yet.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Long-Term Memory Manager
    # -------------------------------------------------------------------------
    render_section_header("Long-Term Memory Inspector", "View, add, or delete personal memory facts.", icon="🧠")

    with st.expander("➕ Add New Long-Term Memory Fact"):
        new_fact = st.text_input("Enter personal fact or memory (e.g. 'User works as a Senior Python Architect')")
        if st.button("Save Memory Fact"):
            if new_fact.strip():
                memory_manager.save_memory(new_fact.strip(), memory_type="user_fact")
                st.success("Memory saved to ChromaDB & SQLite!")
                st.rerun()

    memories = memory_manager.get_all_memories()

    if not memories:
        st.info("No long-term memories saved yet. State personal facts during chat or add one above.")
        return

    for mem in memories:
        m_col1, m_col2, m_col3 = st.columns([4, 2, 1])
        with m_col1:
            st.write(f"🧠 **{mem['content']}**")
        with m_col2:
            st.caption(f"Type: `{mem['memory_type']}` | Saved: {format_timestamp(mem['created_at'])}")
        with m_col3:
            if st.button("🗑️ Delete", key=f"mem_del_{mem['id']}", use_container_width=True):
                memory_manager.delete_memory(mem['id'])
                st.success("Deleted memory!")
                st.rerun()
