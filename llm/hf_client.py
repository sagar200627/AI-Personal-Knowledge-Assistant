"""
Hugging Face API Client
Uses Hugging Face Inference Providers Chat Completion API.
"""

from typing import Generator, Optional

from huggingface_hub import InferenceClient

import config
from utils.logger import get_logger

logger = get_logger("HF_Client")


class HuggingFaceClient:
    """Wrapper around Hugging Face Inference API."""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or config.HF_TOKEN
        self._init_client()

    def update_token(self, token: str) -> None:
        self.api_token = token
        self._init_client()

    def _init_client(self) -> None:
        token = self.api_token.strip() if self.api_token else None

        if not token:
            logger.error("HF_TOKEN is missing.")
            self.client = None
            return

        # Use Hugging Face's automatic provider routing
        self.client = InferenceClient(
            api_key=token,
            provider="auto"
        )

        logger.info("HF Client initialized. Token loaded: True")

    def generate_response(
        self,
        prompt: str,
        model: str = config.DEFAULT_MODEL,
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
        temperature: float = config.DEFAULT_TEMPERATURE,
        top_p: float = config.DEFAULT_TOP_P,
    ) -> str:

        if not self.api_token:
            return (
                "⚠️ Hugging Face token is missing.\n\n"
                "Please check your .env file."
            )

        try:
            logger.info(f"Calling Hugging Face model: {model}")

            response = self.client.chat_completion(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.exception("Hugging Face API request failed")

            # Show the REAL error instead of incorrectly calling
            # every error a token error.
            return (
                "⚠️ Hugging Face API Error\n\n"
                f"Model: {model}\n\n"
                f"Error: {str(e)}"
            )

    def stream_response(
        self,
        prompt: str,
        model: str = config.DEFAULT_MODEL,
        max_tokens: int = config.DEFAULT_MAX_TOKENS,
        temperature: float = config.DEFAULT_TEMPERATURE,
        top_p: float = config.DEFAULT_TOP_P,
    ) -> Generator[str, None, None]:

        if not self.api_token:
            yield "⚠️ Hugging Face token is missing."
            return

        try:

            stream = self.client.chat_completion(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True,
            )

            for chunk in stream:

                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if delta is None:
                    continue

                if delta.content:
                    yield delta.content

        except Exception as e:

            logger.exception("Hugging Face streaming request failed")

            yield (
                "⚠️ Hugging Face API Error\n\n"
                f"Model: {model}\n\n"
                f"Error: {str(e)}"
            )