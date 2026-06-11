from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


def create_chunk(
    db: Session,
    document_id: int,
    chunk_index: int,
    content: str,
    chroma_id: str,
    page_number: int,
    chunk_metadata: dict
):

    chunk = Chunk(
        document_id=document_id,
        chunk_index=chunk_index,
        content=content,
        page_number=page_number,
        chroma_id=chroma_id,
        chunk_metadata=chunk_metadata
    )

    db.add(chunk)

    db.commit()

    db.refresh(chunk)

    return chunk


def create_chunks_bulk(
    db: Session,
    chunks: list
):

    db.add_all(chunks)

    db.commit()


def get_document_chunks(
    db: Session,
    document_id: int
):

    return db.query(Chunk).filter(
        Chunk.document_id == document_id
    ).all()


def get_chunk_by_chroma_id(
    db: Session,
    chroma_id: str
):

    return db.query(Chunk).filter(
        Chunk.chroma_id == chroma_id
    ).first()