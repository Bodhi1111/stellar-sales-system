import asyncio
from core.database.postgres import db_manager
from core.database.models import Base


async def create_tables():
    """Connects to the DB and creates all tables defined in models.py."""
    print("Connecting to database to create tables...")

    # Initialize the manager to get the database engine
    await db_manager.initialize()
    engine = db_manager.engine

    try:
        async with engine.begin() as conn:
            # This line deletes existing tables (for development)
            await conn.run_sync(Base.metadata.drop_all)
            # This line creates the new tables
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
