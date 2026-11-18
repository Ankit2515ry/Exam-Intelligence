"""
LLM Service Module

Responsibilities:
-----------------
1. Connect to Gemini API
2. Send prompts to LLM
3. Return generated responses
4. Handle LLM-related errors

WHY THIS MODULE IS IMPORTANT:
-----------------------------
This module acts as the communication layer
between your backend and the language model.

Pipeline:
---------
Prompt
    ↓
Gemini API
    ↓
Generated Response

This service should ONLY handle:
- LLM interaction
- response generation
- model configuration

NOT:
- retrieval
- chunking
- vector DB operations
"""

import logging

import google.generativeai as genai

from app.config.settings import (
    GOOGLE_API_KEY,
    LLM_MODEL
)

logger = logging.getLogger(__name__)


class LLMProviderError(RuntimeError):
    """Provider failure that must not be counted as a successful answer."""

    def __init__(self, category: str):
        super().__init__(f"LLM provider failure: {category}")
        self.category = category


def _provider_failure_category(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if "timeout" in name or "timeout" in message:
        return "timeout"
    if "quota" in name or "quota" in message or "resourceexhausted" in name:
        return "quota"
    return "provider"


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

"""
Configure Gemini API using environment variables.

IMPORTANT:
----------
Never hardcode API keys directly in code.
"""

genai.configure(
    api_key=GOOGLE_API_KEY
)


# =========================================================
# LOAD MODEL
# =========================================================

"""
Model loaded globally.

WHY?
----
Avoid reloading model for every request.
Improves performance and scalability.
"""

model = genai.GenerativeModel(
    LLM_MODEL
)


# =========================================================
# GENERATE ANSWER
# =========================================================

def generate_answer(
    prompt: str
) -> str:
    """
    Generate response using Gemini.

    PARAMETERS:
    -----------
    prompt:
        Final RAG prompt

    RETURNS:
    --------
    Generated response text
    """

    try:

        response = model.generate_content(
            prompt
        )

        # Safety check
        if not response.text:
            raise LLMProviderError("empty_response")

        return response.text

    except LLMProviderError:
        logger.exception("LLM provider returned no usable response")
        raise
    except Exception as exc:

        # print(
        #     "LLM Error"
        # )
        logger.exception("LLM answer generation failed")

        raise LLMProviderError(_provider_failure_category(exc)) from exc
