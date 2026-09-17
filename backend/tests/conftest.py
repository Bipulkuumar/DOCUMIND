from contextlib import asynccontextmanager
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from pgvector.sqlalchemy import Vector

from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db
import app.db.session as db_session_module

# Map Vector column type to JSON/TEXT when compiling for SQLite in tests
@compiles(Vector, "sqlite")
def compile_vector_sqlite(element, compiler, **kw):
    return "TEXT"


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


fastapi_app.dependency_overrides[get_db] = override_get_db
db_session_module.get_async_session = override_get_async_session


@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as client:
        yield client
