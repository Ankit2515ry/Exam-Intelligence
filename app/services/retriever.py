from app.services.embedder import generate_embedding
from app.services.vectordb import collection


def retrieve_relevant_chunks(question: str, top_k: int = 5):

    # STEP 1: Convert question into embedding
    query_embedding = generate_embedding(question)

    # STEP 2: Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # STEP 3: Format results
    retrieved_chunks = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, metadata, distance in zip(documents, metadatas, distances):

        retrieved_chunks.append({
            "text": doc,
            "metadata": metadata,
            "score": 1 - distance
        })

    return retrieved_chunks