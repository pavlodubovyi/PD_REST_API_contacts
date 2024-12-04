import os
import sys
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.main import app
from app.database import get_db, SessionLocal
from app.models import Base
from dotenv import load_dotenv

# Add the root directory of the project to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv(".env")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://test_user:test_password@localhost/test_db")

# Test database configuration
engine = create_async_engine(DATABASE_URL, echo=True)
TestSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
async def setup_database(db_session):
    """Creates and clears the database before and after each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client():
    """HTTP-client for API testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncSession:
    """Provides a database session for testing"""
    async with SessionLocal() as session:
        print(f"Session type: {type(session)}")
        yield session

app.dependency_overrides[get_db] = db_session
