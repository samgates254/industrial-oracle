import pytest

from industrial_oracle.core.database import DatabaseSessionManager


@pytest.mark.asyncio
async def test_database_without_initialized_engine_is_not_reported_healthy() -> None:
    manager = DatabaseSessionManager("postgresql+asyncpg://invalid")

    assert await manager.check_health() is False
