import chromadb

from app.services.embedder import generate_embedding


client = chromadb.PersistentClient(
    path="app/chroma_db"
)

collection = client.get_or_create_collection(
    name="documents"
)

def get_chunk_by_id(chunk_id: str):

    results = collection.get(
        ids=[chunk_id]
    )

    return results

def delete_document_chunks(document_id: str):

    results = collection.get(

        where={
            "document_id": document_id
        }
    )

    ids = results["ids"]

    if ids:

        collection.delete(
            ids=ids
        )

def search_chunks(query, top_k=5):

    query_embedding = generate_embedding(
        query
    )

    results = collection.query(

        query_embeddings=[query_embedding],

        n_results=top_k
    )

    return results

def get_document_chunks(document_id: str):

    results = collection.get(

        where={
            "document_id": document_id
        }
    )

    return results

def store_chunks(chunks):

    ids = []

    embeddings = []

    documents = []

    metadatas = []

    for chunk in chunks:

        embedding = generate_embedding(
            chunk["text"]
        )

        ids.append(chunk["chunk_id"])

        embeddings.append(embedding)

        documents.append(chunk["text"])

        metadatas.append({
            "chunk_id": chunk["chunk_id"],
            "page": chunk["page"],
            "document_id": chunk["document_id"],
            "chunk_index": chunk["chunk_index"]
        })

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

import chromadb

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_or_create_collection(
    name="exam_intelligence"
)