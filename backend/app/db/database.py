from sqlalchemy import create_engine

from dotenv import load_dotenv

import os


# Load environment variables
load_dotenv()


# PostgreSQL connection URL
DATABASE_URL = os.getenv("DATABASE_URL")


# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL
)