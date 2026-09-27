"""
RAG Engine module.
Combines Vector Retriever (document context), Memory Manager (personal facts), and Hugging Face Client.
Builds contextualized prompts and generates responses.
"""

from typing import List, Dict, Any, Generator, Tuple
from retriever.retriever import VectorRetriever
from memory.memory_manager import MemoryManager
from llm.hf_client import HuggingFaceClient
import config
from utils.logger import get_logger

logger = get_logger("RAGEngine")


class RAGEngine:
    """Retrieval-Augmented Generation (RAG) Engine."""

    def __init__(
        self,
        retriever: VectorRetriever,
        memory_manager: MemoryManager,
        hf_client: HuggingFaceClient,
    ):
        self.retriever = retriever
        self.memory_manager = memory_manager
        self.hf_client = hf_client

    def build_prompt(
        self,
        user_query: str,
        chat_history: List[Dict[str, Any]],
        doc_context_items: List[Dict[str, Any]],
        memory_items: List[Dict[str, Any]],
    ) -> str:
        """Construct a structured prompt incorporating document context and personal memories.

        Args:
            user_query (str): Current user message.
            chat_history (List[Dict[str, Any]]): Previous conversation messages.
            doc_context_items (List[Dict[str, Any]]): Retrieved document chunks.
            memory_items (List[Dict[str, Any]]): Retrieved long-term memories.

        Returns:
            str: System prompt text.
        """
        system_intro = (
            "You are an intelligent, helpful, and concise AI Personal Knowledge Assistant.\n"
            "Answer the user's question accurately based on provided document context and long-term memory facts if available."
        )

        memory_section = ""
        if memory_items:
            mem_lines = [f"- {m['content']}" for m in memory_items]
            memory_section = "\n[LONG-TERM USER MEMORY]\n" + "\n".join(mem_lines) + "\n"

        doc_section = ""
        if doc_context_items:
            doc_lines = []
            for idx, doc in enumerate(doc_context_items, 1):
                doc_lines.append(f"Document [{doc['filename']} - Chunk {doc['chunk_index']}]:\n{doc['content']}")
            doc_section = "\n[RETRIEVED DOCUMENT CONTEXT]\n" + "\n\n".join(doc_lines) + "\n"

        history_section = ""
        if chat_history:
            hist_lines = []
            # Include up to last 6 messages
            recent_history = chat_history[-6:]
            for msg in recent_history:
                role_label = "User" if msg.get("role") == "user" else "Assistant"
                hist_lines.append(f"{role_label}: {msg.get('content', '')}")
            history_section = "\n[RECENT CONVERSATION HISTORY]\n" + "\n".join(hist_lines) + "\n"

        prompt = (
            f"{system_intro}\n"
            f"{memory_section}"
            f"{doc_section}"
            f"{history_section}\n"
            f"User: {user_query}\n"
            f"Assistant:"
        )

        return prompt

    def generate(
        self,
        user_query: str,
        chat_history: List[Dict[str, Any]],
        use_rag: bool = True,
        use_memory: bool = True,
        top_k: int = config.DEFAULT_TOP_K,
        model: str = config.DEFAULT_MODEL,
        temperature: float = config.DEFAULT_TEMPERATURE,
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
        top_p: float = config.DEFAULT_TOP_P,
    ) -> Tuple[Generator[str, None, None], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Perform retrieval and yield streamed response.

        Args:
            user_query (str): User question.
            chat_history (List[Dict[str, Any]]): Conversation history.
            use_rag (bool): Enable document context retrieval.
            use_memory (bool): Enable long-term memory retrieval.
            top_k (int): Number of document chunks to retrieve.
            model (str): Target LLM.
            temperature (float): Sampling temp.
            max_tokens (int): Max token count.
            top_p (float): Top_p threshold.

        Returns:
            Tuple[Generator, List[Dict], List[Dict]]: Token stream generator, retrieved docs, retrieved memories.
        """
        # Auto-extract personal facts into memory
        self.memory_manager.auto_extract_and_save(user_query)

        # Retrieve Document Context
        doc_context = []
        if use_rag:
            doc_context = self.retriever.search_documents(query=user_query, top_k=top_k)

        # Retrieve Memory Context
        memory_context = []
        if use_memory:
            memory_context = self.memory_manager.retrieve_relevant_memories(query=user_query, top_k=3)

        # Build Prompt
        full_prompt = self.build_prompt(
            user_query=user_query,
            chat_history=chat_history,
            doc_context_items=doc_context,
            memory_items=memory_context,
        )

        # Stream response tokens
        stream = self.hf_client.stream_response(
            prompt=full_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        return stream, doc_context, memory_context
