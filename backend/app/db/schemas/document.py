from pydantic import BaseModel

from datetime import datetime


class DocumentCreate(BaseModel):

    title: str

    subject: str


class DocumentResponse(BaseModel):

    id: int

    title: str

    filename: str

    subject: str

    uploaded_by: int

    created_at: datetime

    class Config:

        from_attributes = True