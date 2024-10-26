from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# load sensitive data from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgres://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


# Function for getting database connection
async def get_db():
    async with SessionLocal() as session:
        yield session
