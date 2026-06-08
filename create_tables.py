from app.db.base import Base
from app.db.session import engine

# Import ALL models
from app.db.models.user import User
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.chat_session import ChatSession
from app.db.models.message import Message


# Create all tables
Base.metadata.create_all(bind=engine)

print("Tables created successfully")