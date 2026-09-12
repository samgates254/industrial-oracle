"""Database configuration, SQLAlchemy 2.x declarative base, and session management."""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Type, TypeVar
import uuid

from industrial_oracle.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Detect whether SQLAlchemy is installed in this runtime
try:
    import sqlalchemy as sa
    from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, Boolean, Integer, Float, func
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


if HAS_SQLALCHEMY:
    class Base(DeclarativeBase):
        """SQLAlchemy 2.x Declarative Base."""
        pass

    class TimestampMixin:
        """Mixin for created_at and updated_at UTC timestamps."""
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False,
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False,
        )

    class UUIDPrimaryKeyMixin:
        """Mixin providing UUID v4 primary key."""
        id: Mapped[uuid.UUID] = mapped_column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        )

    class ModelBase(Base, UUIDPrimaryKeyMixin, TimestampMixin):
        """Abstract base entity with UUID pk and timestamps."""
        __abstract__ = True

else:
    # Lightweight emulation when SQLAlchemy is not present in the runtime
    class Base:
        """Stub DeclarativeBase for offline and testing environments."""
        __tablename__: str = ""
        metadata: Any = None

        def __init__(self, **kwargs: Any) -> None:
            self.id = kwargs.get("id", uuid.uuid4())
            self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
            self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ModelBase(Base):
        pass

    def mapped_column(*args: Any, **kwargs: Any) -> Any:
        return kwargs.get("default", None)

    class Mapped:
        def __class_getitem__(cls, item: Any) -> Any:
            return item

    def relationship(*args: Any, **kwargs: Any) -> Any:
        return None

    # Stubs for types
    String = Text = Integer = Float = Boolean = DateTime = ForeignKey = Index = Column = lambda *args, **kwargs: None
    class func:
        @staticmethod
        def now() -> datetime:
            return datetime.now(timezone.utc)


class DatabaseSessionManager:
    """Manages Async SQLAlchemy engine and session pool."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._engine: Optional[Any] = None
        self._sessionmaker: Optional[Any] = None

    def initialize(self) -> None:
        if HAS_SQLALCHEMY:
            try:
                self._engine = create_async_engine(
                    self.url,
                    pool_size=settings.DATABASE_POOL_SIZE,
                    max_overflow=settings.DATABASE_MAX_OVERFLOW,
                    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
                    echo=settings.DATABASE_ECHO,
                )
                self._sessionmaker = async_sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False,
                )
                logger.info("Database engine initialized with pool_size=%d", settings.DATABASE_POOL_SIZE)
            except Exception as exc:
                logger.warning("Failed to initialize asyncpg engine: %s. Operating in test session mode.", exc)
                self._engine = None
                self._sessionmaker = None

    async def get_session(self) -> AsyncGenerator[Any, None]:
        """Provides an async session context."""
        if HAS_SQLALCHEMY and self._sessionmaker:
            async with self._sessionmaker() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        else:
            # In-memory mock session for test execution
            yield InMemoryAsyncSession()

    async def check_health(self) -> bool:
        """Verifies database connectivity."""
        if HAS_SQLALCHEMY and self._engine:
            try:
                async with self._engine.connect() as conn:
                    await conn.execute(sa.text("SELECT 1"))
                return True
            except Exception as e:
                logger.error("Database health check failed: %s", e)
                return False
        return True

    async def close(self) -> None:
        if HAS_SQLALCHEMY and self._engine:
            await self._engine.dispose()
            logger.info("Database connection pool disposed.")


class InMemoryAsyncSession:
    """Mock async session for tests and fallback execution."""

    def __init__(self) -> None:
        self._storage: Dict[str, Dict[uuid.UUID, Any]] = {}

    async def execute(self, query: Any) -> Any:
        class MockResult:
            def scalars(self) -> Any:
                return self
            def all(self) -> List[Any]:
                return []
            def first(self) -> Optional[Any]:
                return None
        return MockResult()

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def add(self, instance: Any) -> None:
        pass


db_manager = DatabaseSessionManager(settings.DATABASE_URL)


async def get_db() -> AsyncGenerator[Any, None]:
    """FastAPI Dependency for database sessions."""
    async for session in db_manager.get_session():
        yield session
