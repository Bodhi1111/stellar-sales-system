#!/usr/bin/env python3
"""
Test RAG retrieval in isolation to identify the exact failure mode.
"""
import asyncio
from agents.sales_copilot.sales_copilot_agent import SalesCopilotAgent
from config.settings import settings

async def test_rag():
    """Test SalesCopilot RAG retrieval"""
    print("=" * 80)
    print("ISOLATED RAG TEST - SalesCopilotAgent")
    print("=" * 80)

    agent = SalesCopilotAgent(settings)

    # Test query
    query = "What client concerns were raised about pricing?"

    print(f"\n📋 Query: {query}")
    print(f"\n🔍 Testing Qdrant search with doc_type filter...\n")

    # Call the agent
    result = await agent.run(data={"query": query})

    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)
    print(result)

    return result

if __name__ == "__main__":
    asyncio.run(test_rag())
