import pytest

from industrial_oracle.core.config import settings
from industrial_oracle.core.redis import RedisManager


@pytest.mark.asyncio
async def test_development_redis_fallback_is_explicit(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    manager = RedisManager("redis://127.0.0.1:1/0")

    await manager.initialize()

    assert manager.using_fallback is True
    assert await (await manager.get_client()).ping() is True
    await manager.close()


@pytest.mark.asyncio
async def test_redis_fallback_is_rejected_outside_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    manager = RedisManager("redis://127.0.0.1:1/0")

    with pytest.raises(RuntimeError, match="required outside development"):
        await manager.initialize()
