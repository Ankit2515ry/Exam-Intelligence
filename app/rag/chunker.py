"""
Chunking Module

Responsibilities:
-----------------
1. Split parsed pages into smaller chunks
2. Preserve semantic continuity using overlap
3. Generate chunk-level metadata
4. Prepare data for embeddings + retrieval

WHY CHUNKING IS IMPORTANT:
--------------------------
Chunking is one of the MOST important parts of RAG.

Bad chunking:
-------------
- broken concepts
- weak retrieval
- hallucinations
- noisy context

Good chunking:
--------------
- better semantic search
- stronger retrieval accuracy
- improved grounding
- lower hallucinations

This module supports:
- source citations
- metadata filtering
- hybrid search
- reranking
"""

import uuid
from typing import List, Dict

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from app.utils.helpers import clean_text

from app.config.settings import (
    CHUNK_SIZE,
    CHUNK_OVERLAP
)


# =========================================================
# TEXT SPLITTER
# =========================================================

"""
Recursive splitter strategy:
----------------------------
Tries splitting using progressively smaller boundaries.

Order:
------
1. Paragraphs
2. Lines
3. Sentences
4. Words

This preserves semantic structure better than:
text[i:i+N]
"""

text_splitter = RecursiveCharacterTextSplitter(

    chunk_size=CHUNK_SIZE,

    chunk_overlap=CHUNK_OVERLAP,

    separators=[
        "\n\n",
        "\n",
        ". ",
        " "
    ]
)


# =========================================================
# CHUNK CREATION
# =========================================================

def create_chunks(
    pages: List[Dict],
    document_id: str
) -> List[Dict]:
    """
    Convert parsed pages into chunks.

    PARAMETERS:
    -----------
    pages:
        Parsed PDF pages

    document_id:
        Unique document identifier

    RETURNS:
    --------
    List of chunk dictionaries
    """

    chunks = []

    chunk_index = 0

    # Iterate through parsed pages
    for page_data in pages:

        page_number = page_data["page"]

        raw_text = page_data["text"]

        # Clean text again for safety
        text = clean_text(raw_text)

        # Skip empty pages
        if not text:
            continue

        # Recursive chunk splitting
        split_texts = text_splitter.split_text(
            text
        )

        # Process each chunk
        for split_text in split_texts:

            # Skip extremely tiny chunks
            if len(split_text.strip()) < 30:
                continue

            # Create chunk object
            chunk = {

                # Unique chunk identifier
                "chunk_id": str(uuid.uuid4()),

                # Parent document
                "document_id": document_id,

                # Chunk content
                "text": split_text,

                # Original PDF page
                "page": page_number,

                # Position inside document
                "chunk_index": chunk_index,

                # Metadata for future retrieval
                "metadata": {

                    "page": page_number,

                    "document_id": document_id,

                    "chunk_index": chunk_index
                }
            }

            chunks.append(chunk)

            chunk_index += 1

    return chunks