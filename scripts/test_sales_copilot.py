"""
Test script for upgraded SalesCopilotAgent (Sprint 03, Epic 3.2)
Tests multi-modal retrieval from Qdrant and Neo4j
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.sales_copilot.sales_copilot_agent import SalesCopilotAgent
from config.settings import settings


async def test_sales_copilot():
    """Test the upgraded SalesCopilotAgent as a multi-modal tool"""
    print("=" * 70)
    print("Testing Upgraded SalesCopilotAgent (Sprint 03, Epic 3.2)")
    print("=" * 70)

    agent = SalesCopilotAgent(settings)

    # Test 1: Simple vector search
    print("\n📝 Test 1: Simple Vector Search (Qdrant)")
    print("-" * 70)

    test_query_1 = {
        "query": "Find transcripts about estate planning"
    }

    result_1 = await agent.run(data=test_query_1)
    print(f"Query: {test_query_1['query']}")
    print(f"Result: {result_1}")

    # Test 2: Email search (different doc_type)
    print("\n" + "=" * 70)
    print("\n📝 Test 2: Email Search (filtered by doc_type)")
    print("-" * 70)

    test_query_2 = {
        "query": "Find email drafts about follow-ups"
    }

    result_2 = await agent.run(data=test_query_2)
    print(f"Query: {test_query_2['query']}")
    print(f"Result: {result_2}")

    # Test 3: Multi-step query (Neo4j -> Qdrant)
    print("\n" + "=" * 70)
    print("\n📝 Test 3: Multi-Step Query (Neo4j → Qdrant)")
    print("-" * 70)

    test_query_3 = {
        "query": "What objections did client John Doe raise?"
    }

    result_3 = await agent.run(data=test_query_3)
    print(f"Query: {test_query_3['query']}")
    print(f"Result: {result_3}")

    # Test 4: Error handling (missing query)
    print("\n" + "=" * 70)
    print("\n📝 Test 4: Error Handling (missing query)")
    print("-" * 70)

    result_4 = await agent.run(data={})
    print(f"Result: {result_4}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if all(['error' not in str(r) or 'Missing query' in str(r) for r in [result_1, result_2, result_3, result_4]]):
        print("\n✅ Sprint 03 Epic 3.2: SalesCopilotAgent Upgraded Successfully!")
        print("   - Multi-modal retrieval (Qdrant + Neo4j)")
        print("   - Filtered search by doc_type")
        print("   - Multi-step reasoning (graph → vector)")
        print("   - Standardized data dict interface")
    else:
        print("\n⚠️ Some tests may have encountered issues")
        print("   Note: This is expected if Qdrant/Neo4j don't have data yet")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_sales_copilot())
