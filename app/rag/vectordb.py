"""
Vector Database Module

Responsibilities:
-----------------
1. Store embeddings in ChromaDB
2. Perform semantic similarity search
3. Handle metadata filtering
4. Retrieve stored chunks
5. Delete document vectors

WHY VECTOR DB IS IMPORTANT:
---------------------------
The vector database powers semantic retrieval.

Workflow:
---------
Chunk
    ↓
Embedding
    ↓
Vector DB
    ↓
Similarity Search
    ↓
Retrieved Context

This module is the foundation of:
- RAG retrieval
- metadata filtering
- source citations
- hybrid search
- reranking
"""

from typing import List, Dict, Optional

import chromadb

from app.rag.embedder import (
    generate_embedding,
    generate_embeddings
)

from app.config.settings import (
    VECTOR_DB_DIR,
    COLLECTION_NAME
)


# =========================================================
# CHROMA CLIENT
# =========================================================

"""
Persistent database storage.

WHY PERSISTENT?
---------------
Without persistence:
server restart → all vectors lost

PersistentClient stores vectors on disk.
"""

client = chromadb.PersistentClient(
    path=VECTOR_DB_DIR
)


# =========================================================
# COLLECTION
# =========================================================

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


# =========================================================
# STORE CHUNKS
# =========================================================

def store_chunks(
    chunks: List[Dict]
) -> None:
    """
    Store chunks inside ChromaDB.

    PROCESS:
    --------
    chunks
        ↓
    embeddings
        ↓
    vector storage
    """

    if not chunks:
        return

    ids = []

    documents = []

    metadatas = []

    texts = []

    # Prepare batch data
    for chunk in chunks:

        ids.append(
            chunk["chunk_id"]
        )

        documents.append(
            chunk["text"]
        )

        texts.append(
            chunk["text"]
        )

        metadatas.append({

            "chunk_id": chunk["chunk_id"],

            "document_id": (
                chunk["document_id"]
            ),

            "page": chunk["page"],

            "chunk_index": (
                chunk["chunk_index"]
            )
        })

    # Batch embedding generation
    embeddings = generate_embeddings(
        texts
    )

    # Store in ChromaDB
    collection.add(

        ids=ids,

        embeddings=embeddings,

        documents=documents,

        metadatas=metadatas
    )


# =========================================================
# SEMANTIC SEARCH
# =========================================================

def search_chunks(
    query: str,
    top_k: int = 5,
    document_id: Optional[str] = None
) -> Dict:
    """
    Perform semantic vector search.

    PARAMETERS:
    -----------
    query:
        User question

    top_k:
        Number of retrieved chunks

    document_id:
        Optional metadata filter

    RETURNS:
    --------
    ChromaDB query results
    """

    query_embedding = generate_embedding(
        query
    )

    # Metadata filtering support
    if document_id:

        results = collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=top_k,

            where={
                "document_id": document_id
            }
        )

    else:

        results = collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=top_k
        )

    return results


# =========================================================
# GET DOCUMENT CHUNKS
# =========================================================

def get_document_chunks(
    document_id: str
) -> Dict:
    """
    Retrieve all chunks belonging
    to a document.
    """

    results = collection.get(

        where={
            "document_id": document_id
        }
    )

    return results


# =========================================================
# GET CHUNK BY ID
# =========================================================

def get_chunk_by_id(
    chunk_id: str
) -> Dict:
    """
    Retrieve a single chunk
    using chunk ID.
    """

    results = collection.get(

        ids=[chunk_id]
    )

    return results


# =========================================================
# DELETE DOCUMENT
# =========================================================

def delete_document_chunks(
    document_id: str
) -> None:
    """
    Delete all chunks belonging
    to a document.
    """

    results = collection.get(

        where={
            "document_id": document_id
        }
    )

    ids = results.get("ids", [])

    if ids:

        collection.delete(
            ids=ids
        )