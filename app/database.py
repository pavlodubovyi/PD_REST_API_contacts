from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load sensitive data from .env
load_dotenv()

# Database URL for connecting to the PostgreSQL database
DATABASE_URL = os.getenv("DATABASE_URL")

# Create an asynchronous engine for connecting to the database
engine = create_async_engine(DATABASE_URL, echo=True)

# Configure the session maker to use the asynchronous session class
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Define the base class for the ORM models
Base = declarative_base()


async def get_db():
    """
    Provides a database session for dependency injection in route handlers.

    This function is designed to be used as a dependency in FastAPI routes,
    yielding a database session that can be used within request handlers.
    The session is automatically closed after the request is processed.

    :yield: A database session.
    :rtype: AsyncSession
    """
    async with SessionLocal() as session:
        yield session
