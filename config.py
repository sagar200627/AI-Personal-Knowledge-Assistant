"""
Configuration module for AI Personal Knowledge Assistant.
Defines paths, environment variables, default model settings, and app constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
SESSIONS_DIR = BASE_DIR / "sessions"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [DATA_DIR, UPLOADS_DIR, SESSIONS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_PATH = DATA_DIR / "app.db"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# API & Model Settings
HF_TOKEN = os.getenv("HF_TOKEN", "")
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

AVAILABLE_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "meta-llama/Llama-3.2-3B-Instruct",
]

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# RAG & Chunking Parameters
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 3

# Generation Hyperparameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TOP_P = 0.9

# Application Details
APP_TITLE = "AI Personal Knowledge Assistant"
APP_SUBTITLE = "Production-Ready AI Agent with Long-Term Memory, RAG & Document Intelligence"
APP_VERSION = "1.0.0"
