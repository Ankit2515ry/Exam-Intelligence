from sqlalchemy import create_engine

from app.config.environment import load_application_environment

import os


# Load environment variables
load_application_environment()


# PostgreSQL connection URL
DATABASE_URL = os.getenv("DATABASE_URL")


# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL
)
