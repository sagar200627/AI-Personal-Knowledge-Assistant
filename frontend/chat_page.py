"""
Chat Page UI Component.
Renders AI chat streaming interface, chat session sidebar controls, RAG toggles, and export features.
"""

import streamlit as st
from database.db_manager import DatabaseManager
from rag.rag_engine import RAGEngine
from export.export_manager import ExportManager
from frontend.components import render_hero_banner
import config
from utils.logger import get_logger

logger = get_logger("ChatPage")


def render_chat_page(db: DatabaseManager, rag_engine: RAGEngine) -> None:
    """Render main AI Chat tab with streaming responses and session history."""
    render_hero_banner(
        title="💬 AI Knowledge Assistant",
        subtitle="Chat with long-term memory recall and real-time document context.",
    )

    # -------------------------------------------------------------------------
    # Sidebar: Session List & Controls
    # -------------------------------------------------------------------------
    st.sidebar.markdown("### 🗂️ Chat Sessions")

    if st.sidebar.button("➕ New Chat Session", use_container_width=True):
        new_id = db.create_session(title="New Conversation")
        st.session_state.current_session_id = new_id
        st.rerun()

    sessions = db.get_sessions()
    if not sessions:
        # Create default initial session if none exists
        init_id = db.create_session(title="Welcome Session")
        st.session_state.current_session_id = init_id
        sessions = db.get_sessions()

    # Ensure valid current session
    if "current_session_id" not in st.session_state or not st.session_state.current_session_id:
        st.session_state.current_session_id = sessions[0]["id"]

    session_dict = {s["id"]: s["title"] for s in sessions}

    # Session Selector Dropdown in Sidebar
    selected_id = st.sidebar.selectbox(
        "Select Session",
        options=list(session_dict.keys()),
        format_func=lambda x: session_dict.get(x, "Session"),
        index=list(session_dict.keys()).index(st.session_state.current_session_id)
        if st.session_state.current_session_id in session_dict
        else 0,
    )
    st.session_state.current_session_id = selected_id

    # Rename & Delete Controls
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        with st.popover("✏️ Rename"):
            new_title = st.text_input("New Session Title", value=session_dict.get(selected_id, ""))
            if st.button("Save Title"):
                if new_title.strip():
                    db.rename_session(selected_id, new_title.strip())
                    st.success("Renamed!")
                    st.rerun()
    with col_s2:
        if st.button("🗑️ Delete", use_container_width=True):
            if len(sessions) > 1:
                db.delete_session(selected_id)
                st.session_state.current_session_id = None
                st.rerun()
            else:
                st.sidebar.warning("Cannot delete only active session.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ RAG & Memory Settings")
    use_rag = st.sidebar.toggle("📄 Enable Document RAG", value=True)
    use_memory = st.sidebar.toggle("🧠 Enable Long-Term Memory", value=True)
    top_k = st.sidebar.slider("Top K Retrieved Chunks", min_value=1, max_value=10, value=config.DEFAULT_TOP_K)

    selected_model = st.sidebar.selectbox(
        "AI Model",
        options=config.AVAILABLE_MODELS,
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Export Chat")
    exp_col1, exp_col2 = st.sidebar.columns(2)

    # Fetch Messages for Active Session
    messages = db.get_messages(st.session_state.current_session_id)

    with exp_col1:
        txt_data = ExportManager.export_to_txt(
            session_title=session_dict.get(st.session_state.current_session_id, "Chat"),
            messages=messages,
        )
        st.download_button(
            label="📄 TXT",
            data=txt_data,
            file_name=f"chat_{st.session_state.current_session_id[:6]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with exp_col2:
        md_data = ExportManager.export_to_markdown(
            session_title=session_dict.get(st.session_state.current_session_id, "Chat"),
            messages=messages,
        )
        st.download_button(
            label="📝 MD",
            data=md_data,
            file_name=f"chat_{st.session_state.current_session_id[:6]}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # -------------------------------------------------------------------------
    # Main Chat View
    # -------------------------------------------------------------------------
    # Render Chat History
    for msg in messages:
        role = msg["role"]
        with st.chat_message(role):
            st.markdown(msg["content"])
            if msg.get("context_used"):
                with st.expander("🔍 View Retrieved Context / Memories"):
                    st.info(msg["context_used"])

    # Chat Input Box
    user_input = st.chat_input("Ask a question, upload facts, or search documents...")

    if user_input:
        # Render User Message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Save User Message to Database
        db.add_message(
            session_id=st.session_state.current_session_id,
            role="user",
            content=user_input,
        )

        # Auto-update session title if default
        if session_dict.get(st.session_state.current_session_id) in ["New Chat Session", "New Conversation", "Welcome Session"]:
            short_title = user_input[:25] + "..." if len(user_input) > 25 else user_input
            db.rename_session(st.session_state.current_session_id, short_title)

        # Generate Assistant Streaming Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            try:
                token_stream, doc_context, memory_context = rag_engine.generate(
                    user_query=user_input,
                    chat_history=messages,
                    use_rag=use_rag,
                    use_memory=use_memory,
                    top_k=top_k,
                    model=selected_model,
                )

                # Format retrieved context summary
                context_summary_lines = []
                if doc_context:
                    context_summary_lines.append("**Retrieved Document Chunks:**")
                    for d in doc_context:
                        context_summary_lines.append(f"- *{d['filename']}* (score {d['score']}): {d['content'][:120]}...")
                if memory_context:
                    context_summary_lines.append("**Retrieved Long-Term Memories:**")
                    for m in memory_context:
                        context_summary_lines.append(f"- *Memory* (score {m['score']}): {m['content']}")

                context_summary_str = "\n".join(context_summary_lines) if context_summary_lines else None

                full_response = ""
                for token in token_stream:
                    full_response += token
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

                if context_summary_str:
                    with st.expander("🔍 View Retrieved Context / Memories"):
                        st.info(context_summary_str)

                # Save Assistant Message to Database
                db.add_message(
                    session_id=st.session_state.current_session_id,
                    role="assistant",
                    content=full_response,
                    context_used=context_summary_str,
                )

            except Exception as e:
                logger.error(f"Chat generation error: {e}")
                st.error(f"Error generating response: {str(e)}")
