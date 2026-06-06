"""
Initialize PostgreSQL tables
"""

from app.db.database import engine

from app.db.base import Base


# Import all models here
from app.db.models.user import User


# Create tables
Base.metadata.create_all(bind=engine)

print("Tables created successfully")