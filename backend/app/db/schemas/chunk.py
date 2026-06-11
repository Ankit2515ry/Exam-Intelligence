from pydantic import BaseModel

from typing import Dict


class ChunkCreate(BaseModel):

    document_id: int

    chunk_index: int

    content: str

    chroma_id: str

    chunk_metadata: Dict


class ChunkResponse(BaseModel):

    id: int

    document_id: int

    chunk_index: int

    content: str

    chroma_id: str

    chunk_metadata: Dict

    class Config:

        from_attributes = True