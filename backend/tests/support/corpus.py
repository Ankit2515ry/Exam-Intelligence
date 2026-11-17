"""Small, explicitly synthetic corpora; no uploaded user data is read."""

DOCUMENT_A = "11111111-1111-4111-8111-111111111111"
DOCUMENT_B = "22222222-2222-4222-8222-222222222222"


def make_chunk(document_id=DOCUMENT_A, user_id=7, index=0, text=None):
    return {
        "chunk_id": f"{document_id}-{user_id}-{index}",
        "document_id": document_id,
        "text": text or f"Database normalization reduces redundant relational data. Example {index}.",
        "page": index + 1,
        "chunk_index": index,
        "metadata": {
            "document_uuid": document_id,
            "user_id": user_id,
            "page": index + 1,
            "chunk_index": index,
        },
    }


def scope_corpus():
    return [
        make_chunk(DOCUMENT_A, 7, 0),
        make_chunk(DOCUMENT_A, 7, 1),
        make_chunk(DOCUMENT_B, 7, 0),
        make_chunk(DOCUMENT_B, 7, 1),
        make_chunk(DOCUMENT_B, 8, 0),
    ]
