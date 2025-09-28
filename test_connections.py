import asyncio
from core.database.postgres import db_manager
from core.database.neo4j import neo4j_manager

async def test_connections():
    print("Testing database connections...")

    # Test PostgreSQL
    try:
        await db_manager.initialize()
        async with db_manager.session_context() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"❌ PostgreSQL failed: {e}")

    # Test Neo4j
    try:
        result = await neo4j_manager.execute_query("RETURN 1 as num")
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"❌ Neo4j failed: {e}")

    # Cleanup
    await db_manager.close()
    await neo4j_manager.close()

if __name__ == "__main__":
    asyncio.run(test_connections())