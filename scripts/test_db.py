import asyncio
from sqlalchemy import text
from core.database.postgres import db_manager # Importing our new manager

async def main():
    """
    Initializes the db manager and tests the connection with a query.
    """
    try:
        # The manager will auto-initialize on the first session request
        async with db_manager.session_context() as session:
            print("✅ Acquired a session from the connection pool.")

            # Execute a simple query to confirm the session works
            result = await session.execute(text("SELECT 1"))
            value = result.scalar_one()

            if value == 1:
                print(f"✅ Test query successful! (SELECT 1 returned {value})")
            else:
                print(f"❌ Test query failed.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        # Cleanly close the entire connection pool
        await db_manager.close()

if __name__ == "__main__":
    print("--- Running Database Manager Test ---")
    asyncio.run(main())
    print("--- Test Finished ---")