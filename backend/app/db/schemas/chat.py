from pydantic import BaseModel

from datetime import datetime


class ChatSessionCreate(BaseModel):

    title: str


class MessageCreate(BaseModel):

    role: str

    content: str


class MessageResponse(BaseModel):

    id: int

    role: str

    content: str

    created_at: datetime

    class Config:

        from_attributes = True