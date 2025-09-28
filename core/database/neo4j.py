import asyncio
import logging
import time
from neo4j import AsyncGraphDatabase
from config.settings import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Neo4jManager:
    _instance = None
    _driver = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.uri = settings.NEO4J_URL
            self.user = settings.NEO4J_USER
            self.password = settings.NEO4J_PASSWORD
            self.initialized = True

    async def _get_driver(self):
        async with self._lock:
            if self._driver is None:
                max_retries = 3
                retry_delay = 2

                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting to connect to Neo4j at {self.uri} (attempt {attempt + 1}/{max_retries})")
                        start_time = time.time()

                        self._driver = AsyncGraphDatabase.driver(
                            self.uri,
                            auth=(self.user, self.password),
                            connection_acquisition_timeout=15,
                            connection_timeout=15,
                            max_connection_pool_size=10
                        )

                        # Verify connectivity with timeout
                        logger.debug("Verifying Neo4j connectivity...")
                        await asyncio.wait_for(
                            self._driver.verify_connectivity(),
                            timeout=10.0
                        )

                        elapsed = time.time() - start_time
                        logger.info(f"✅ Neo4j driver initialized successfully in {elapsed:.2f}s")
                        return self._driver

                    except asyncio.TimeoutError:
                        logger.error(f"Neo4j connection timeout on attempt {attempt + 1}")
                    except Exception as e:
                        logger.error(f"Failed to initialize Neo4j driver (attempt {attempt + 1}): {type(e).__name__}: {e}")

                    # Clean up failed connection
                    if self._driver:
                        try:
                            await self._driver.close()
                        except:
                            pass
                        self._driver = None

                    # Wait before retry (except on last attempt)
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {retry_delay}s before retry...")
                        await asyncio.sleep(retry_delay)

                # All retries failed
                raise ConnectionError(f"Failed to connect to Neo4j after {max_retries} attempts")

            return self._driver

    async def execute_query(self, query: str, parameters: dict = None):
        """Execute a query with proper error handling and connection management (backward compatible)"""
        logger.debug(f"Executing query: {query[:100]}...")

        try:
            driver = await self._get_driver()
            async with driver.session(database="neo4j") as session:
                result = await session.run(query, parameters or {})
                consumed = await result.consume()
                logger.debug(f"Query executed successfully")
                return consumed
        except ConnectionError:
            logger.error("Neo4j connection failed after all retries")
            raise
        except Exception as e:
            logger.error(f"Neo4j query failed: {type(e).__name__}: {e}")
            # If connection is bad, reset the driver
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                logger.info("Resetting Neo4j driver due to connection error")
                await self._reset_driver()
            raise

    async def execute_read_query(self, query: str, parameters: dict = None):
        """Execute a read-only query"""
        driver = await self._get_driver()
        try:
            async with driver.session(database="neo4j") as session:
                result = await session.run(query, parameters or {})
                return [record.data() for record in await result.data()]
        except Exception as e:
            logger.error(f"Neo4j read query failed: {e}")
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                await self._reset_driver()
            raise

    async def execute_write_query(self, query: str, parameters: dict = None):
        """Execute a write query"""
        driver = await self._get_driver()
        try:
            async with driver.session(database="neo4j") as session:
                async with session.begin_transaction() as tx:
                    result = await tx.run(query, parameters or {})
                    return await result.consume()
        except Exception as e:
            logger.error(f"Neo4j write query failed: {e}")
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                await self._reset_driver()
            raise

    async def _reset_driver(self):
        """Reset the driver connection"""
        async with self._lock:
            if self._driver:
                try:
                    await self._driver.close()
                except:
                    pass
                self._driver = None
            logger.info("Neo4j driver reset")

    async def close(self):
        """Close the driver connection"""
        async with self._lock:
            if self._driver:
                try:
                    await self._driver.close()
                    logger.info("Neo4j driver closed")
                except Exception as e:
                    logger.error(f"Error closing Neo4j driver: {e}")
                finally:
                    self._driver = None

    async def health_check(self):
        """Check if Neo4j is healthy"""
        try:
            driver = await self._get_driver()
            await driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

# Global instance
neo4j_manager = Neo4jManager()