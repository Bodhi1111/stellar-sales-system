from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config.settings import settings

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.session_maker = None

    async def initialize(self):
        """Initializes the database engine and session pool."""
        if not self.engine:
            db_url = (
                f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
                f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )
            self.engine = create_async_engine(db_url, pool_size=10, max_overflow=5)
            self.session_maker = sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
            print("✅ Database connection pool initialized.")

    async def close(self):
        """Closes the database engine."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_maker = None
            print("❌ Database connection pool closed.")

    @asynccontextmanager
async def session_context(self):
    """Provides a clean way to handle database sessions."""
    if not self.session_maker:
        await self.initialize()

    session = self.session_maker()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Create a single, global instance that the whole app can share
db_manager = DatabaseManager()