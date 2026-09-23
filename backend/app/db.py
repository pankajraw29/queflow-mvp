"""MongoDB connection (Motor, async)."""
from motor.motor_asyncio import AsyncIOMotorClient

from .config import DB_NAME, MONGO_URL

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


async def get_db():
    """FastAPI dependency. Override in tests with an in-memory fake."""
    return get_client()[DB_NAME]
