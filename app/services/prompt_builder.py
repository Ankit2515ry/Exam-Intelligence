def build_prompt(question: str, retrieved_chunks: list):

    context = "\n\n".join(
        [chunk["text"] for chunk in retrieved_chunks]
    )

    prompt = f"""
You are an AI tutor.

Answer the question ONLY using the provided context.

If the answer is not present in the context, say:
"I could not find the answer in the provided material."

Context:
---------
{context}
---------

Question:
{question}

Answer:
"""

    return prompt