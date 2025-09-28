#!/usr/bin/env python3
"""Diagnose Neo4j connectivity issues"""

import asyncio
import socket
import time
from neo4j import AsyncGraphDatabase
import subprocess

def check_port(host, port):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

async def test_basic_connection():
    """Test basic Neo4j connection"""
    print("\n1. Testing Basic Connection...")
    print("-" * 40)

    # Check if port is open
    if check_port("127.0.0.1", 7687):
        print("✅ Port 7687 is open")
    else:
        print("❌ Port 7687 is closed")
        return False

    # Test different connection methods
    test_configs = [
        ("bolt://127.0.0.1:7687", "IPv4 explicit"),
        ("bolt://localhost:7687", "localhost"),
        ("neo4j://127.0.0.1:7687", "neo4j protocol"),
    ]

    for uri, desc in test_configs:
        try:
            print(f"\nTesting {desc} ({uri})...")
            start = time.time()
            driver = AsyncGraphDatabase.driver(
                uri,
                auth=("neo4j", "password"),
                connection_acquisition_timeout=5
            )
            await driver.verify_connectivity()
            elapsed = time.time() - start
            print(f"  ✅ Connected in {elapsed:.2f}s")
            await driver.close()
        except Exception as e:
            print(f"  ❌ Failed: {type(e).__name__}: {str(e)[:100]}")

    return True

async def test_concurrent_connections():
    """Test multiple concurrent connections"""
    print("\n2. Testing Concurrent Connections...")
    print("-" * 40)

    async def connect_and_query(id: int):
        try:
            driver = AsyncGraphDatabase.driver(
                "bolt://127.0.0.1:7687",
                auth=("neo4j", "password"),
                connection_acquisition_timeout=10
            )
            async with driver.session() as session:
                result = await session.run("RETURN $id as id", {"id": id})
                data = await result.single()
                await driver.close()
                return f"Connection {id}: ✅"
        except Exception as e:
            return f"Connection {id}: ❌ {type(e).__name__}"

    # Test 5 concurrent connections
    tasks = [connect_and_query(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    for result in results:
        print(f"  {result}")

async def test_with_manager():
    """Test using the actual Neo4j manager"""
    print("\n3. Testing with Neo4j Manager...")
    print("-" * 40)

    try:
        from core.database.neo4j import neo4j_manager

        # Test health check
        print("Testing health check...")
        healthy = await neo4j_manager.health_check()
        print(f"  Health check: {'✅' if healthy else '❌'}")

        # Test a simple query
        print("Testing simple query...")
        result = await neo4j_manager.execute_query("RETURN 1 as num")
        print(f"  Query executed: ✅")

        # Test cleanup
        await neo4j_manager.close()
        print(f"  Cleanup: ✅")

    except Exception as e:
        print(f"  ❌ Manager test failed: {type(e).__name__}: {e}")

def check_docker_status():
    """Check Docker container status"""
    print("\n4. Docker Container Status...")
    print("-" * 40)

    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=stellar_neo4j", "--format", "table {{.Status}}"],
            capture_output=True,
            text=True
        )
        if "Up" in result.stdout:
            print("✅ Neo4j container is running")

            # Get container logs
            logs = subprocess.run(
                ["docker", "logs", "stellar_neo4j", "--tail", "5"],
                capture_output=True,
                text=True
            )
            print("\nRecent logs:")
            print(logs.stdout)
        else:
            print("❌ Neo4j container is not running")
    except Exception as e:
        print(f"❌ Could not check Docker status: {e}")

async def main():
    print("=" * 50)
    print("NEO4J CONNECTIVITY DIAGNOSTICS")
    print("=" * 50)

    check_docker_status()

    if await test_basic_connection():
        await test_concurrent_connections()
        await test_with_manager()

    print("\n" + "=" * 50)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())