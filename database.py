
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Load settings from the .env file.
load_dotenv()

# PostgreSQL connection details.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=os.getenv("DATABASE_PASSWORD"),
    host="localhost",
    port=5432,
    database=os.getenv("DATABASE_NAME", "backend_db"),
)

# Create the database engine.
engine = create_engine(DATABASE_URL)

# Create sessions for database operations.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
