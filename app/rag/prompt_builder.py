"""
Prompt Builder Module
"""

from typing import List

from langchain_core.documents import Document


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    question: str,
    retrieved_chunks: List[Document]
) -> str:
    """
    Build grounded RAG prompt.
    """

    # =====================================================
    # BUILD CONTEXT
    # =====================================================

    context = "\n\n".join(

        chunk.page_content

        for chunk in retrieved_chunks
    )

    # =====================================================
    # FINAL PROMPT
    # =====================================================

    prompt = f"""
You are an intelligent AI tutor helping students learn from uploaded study materials.

IMPORTANT INSTRUCTIONS:
-----------------------

1. Use the provided context as the PRIMARY source of truth.

2. If the answer is clearly available in the context:
   - answer using the context
   - explain clearly
   - stay grounded in the material

3. If the context is partially incomplete:
   - you may use your own knowledge ONLY to supplement missing details
   - keep the answer educational and accurate
   - prioritize consistency with the retrieved material

4. If the answer is completely unrelated to the provided context:
   - clearly mention that the answer was not found in the uploaded material
   - then provide a general educational answer if possible

5. Never fabricate citations or pretend information came from the context when it did not.

6. Keep answers:
   - clear
   - structured
   - student-friendly

CONTEXT:
---------
{context}
---------

QUESTION:
---------
{question}
---------

ANSWER:
"""

    return prompt