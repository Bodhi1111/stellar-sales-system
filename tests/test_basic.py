import pytest
from core.database.postgres import db_manager
from sqlalchemy import text

@pytest.mark.asyncio
async def test_db_connection():
    await db_manager.initialize()
    async with db_manager.session_context() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    await db_manager.close()

# Add more tests here
