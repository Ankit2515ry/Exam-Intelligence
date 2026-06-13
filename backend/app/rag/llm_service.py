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

import google.generativeai as genai

from app.config.settings import (
    GOOGLE_API_KEY,
    LLM_MODEL
)


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

            return (
                "Unable to generate response."
            )

        return response.text

    except Exception as error:

        # print(
        #     f"LLM Error: {error}"
        # )

        return (
            "An error occurred while "
            "generating the response."
        )