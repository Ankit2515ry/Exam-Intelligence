from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    JSON
)

from sqlalchemy.orm import relationship

from app.db.base import Base


class Chunk(Base):

    __tablename__ = "chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id")
    )

    chunk_index = Column(Integer)

    page_number = Column(Integer)
    
    content = Column(Text)

    chroma_id = Column(String)

    chunk_metadata = Column(JSON)

    document = relationship(
        "Document",
        back_populates="chunks"
    )