import io
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_session
from app.main import create_app
from app.storage import get_storage


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    def signed_url(self, key: str) -> str:
        return f"https://objects.test/{key}?signed=1"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        database_url="sqlite+aiosqlite://",
    )


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory, settings: Settings) -> AsyncIterator[AsyncClient]:
    storage = FakeStorage()
    app = create_app()

    async def test_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_storage] = lambda: storage
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        http.storage = storage  # type: ignore[attr-defined]
        yield http


@pytest.fixture
def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (100, 50), "white").save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def valid_draft() -> dict:
    return {
        "widthMeters": 10.0,
        "heightMeters": 5.0,
        "walkableAreas": [
            {
                "id": "walk_1",
                "points": [
                    {"x": 0.0, "y": 0.0},
                    {"x": 10.0, "y": 0.0},
                    {"x": 10.0, "y": 5.0},
                    {"x": 0.0, "y": 5.0},
                ],
            }
        ],
        "obstacles": [],
        "destinations": [
            {"id": "dst_1", "name": "Entrance", "x": 1.0, "y": 1.0, "nodeId": "n1"},
            {"id": "dst_2", "name": "Office", "x": 9.0, "y": 1.0, "nodeId": "n2"},
        ],
        "routeNodes": [
            {"id": "n1", "x": 1.0, "y": 1.0, "type": "DOOR"},
            {"id": "n2", "x": 9.0, "y": 1.0, "type": "DOOR"},
        ],
        "routeEdges": [
            {
                "id": "e1",
                "fromNodeId": "n1",
                "toNodeId": "n2",
                "distanceMeters": 999.0,
                "accessible": True,
                "temporarilyClosed": False,
            },
            {
                "id": "e2",
                "fromNodeId": "n2",
                "toNodeId": "n1",
                "distanceMeters": 999.0,
                "accessible": True,
                "temporarilyClosed": False,
            },
        ],
    }
