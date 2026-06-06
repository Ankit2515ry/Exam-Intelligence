from sqlalchemy.orm import sessionmaker

from app.db.database import engine


# Database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Dependency for database session
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()