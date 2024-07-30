import contextlib
from typing import Any
from typing import AsyncIterator

from core.config import settings
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import as_declarative
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import mapped_column


@as_declarative()
class Base:
    id: Mapped[int] = mapped_column('id', primary_key=True, sort_order=-1)

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any]):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        if self._engine is None:
            raise Exception('DatabaseSessionManager is not initialized')
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception('DatabaseSessionManager is not initialized')

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception('DatabaseSessionManager is not initialized')

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def get_engine(self):
        return self._engine


sessionmanager: DatabaseSessionManager = DatabaseSessionManager(
    settings.DATABASE_URL, {'echo': settings.DEBUG}
)
