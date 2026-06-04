from pydantic import BaseModel
from typing import Optional
from typing import Dict


class Chunk(BaseModel):

    chunk_id: str

    document_id: str

    text: str

    page: int

    chunk_index: int

    chapter: Optional[str] = None

    section: Optional[str] = None

    metadata: Optional[Dict] = None