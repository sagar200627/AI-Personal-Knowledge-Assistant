"""
Settings Page UI Component.
Manages Hugging Face API Token, Model selections, hyperparameter presets, and RAG configuration.
"""

import os
import streamlit as st
import config
from llm.hf_client import HuggingFaceClient
from frontend.components import render_hero_banner, render_section_header
from utils.logger import get_logger

logger = get_logger("SettingsPage")


def render_settings_page(hf_client: HuggingFaceClient) -> None:
    """Render Settings and API Configuration tab."""
    render_hero_banner(
        title="⚙️ Application Settings",
        subtitle="Manage Hugging Face API Keys, default models, RAG parameters, and generation presets.",
    )

    # -------------------------------------------------------------------------
    # Hugging Face API Token Management
    # -------------------------------------------------------------------------
    render_section_header("Hugging Face API Key", "Configure your HF Serverless Inference API token.", icon="🔑")

    current_token = st.session_state.get("hf_token", config.HF_TOKEN)

    token_input = st.text_input(
        "Hugging Face Token (HF_TOKEN)",
        value=current_token,
        type="password",
        help="Get a free token from https://huggingface.co/settings/tokens",
    )

    if st.button("💾 Save API Token"):
        st.session_state.hf_token = token_input.strip()
        hf_client.update_token(token_input.strip())
        st.success("Hugging Face API Token updated successfully!")
        st.rerun()

    if not current_token:
        st.warning("⚠️ No API Token configured. Hugging Face free tier calls may be restricted or fail.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Default Model & Hyperparameters
    # -------------------------------------------------------------------------
    render_section_header("LLM Model & Generation Presets", "Tune text generation hyperparameters.", icon="🎛️")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        default_model = st.selectbox(
            "Default Inference Model",
            options=config.AVAILABLE_MODELS,
            index=0,
        )

        max_tokens = st.slider(
            "Max Output Tokens",
            min_value=128,
            max_value=4096,
            value=config.DEFAULT_MAX_TOKENS,
            step=128,
        )

    with col_m2:
        temperature = st.slider(
            "Temperature (Creativity)",
            min_value=0.0,
            max_value=2.0,
            value=config.DEFAULT_TEMPERATURE,
            step=0.05,
        )

        top_p = st.slider(
            "Top-P (Nucleus Sampling)",
            min_value=0.0,
            max_value=1.0,
            value=config.DEFAULT_TOP_P,
            step=0.05,
        )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # System Status & Paths
    # -------------------------------------------------------------------------
    render_section_header("System Environment", "System directory paths and active databases.", icon="🖥️")

    st.json(
        {
            "Application Version": config.APP_VERSION,
            "SQLite Database Path": str(config.DB_PATH),
            "ChromaDB Storage Directory": str(config.CHROMA_DB_DIR),
            "Uploads Directory": str(config.UPLOADS_DIR),
            "Embedding Model": config.EMBEDDING_MODEL_NAME,
        }
    )
