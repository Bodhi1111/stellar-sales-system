#!/usr/bin/env python3
"""
Test RAG retrieval with Joe Lotito transcript.
"""
import asyncio
from agents.sales_copilot.sales_copilot_agent import SalesCopilotAgent
from config.settings import settings

async def test_rag():
    """Test SalesCopilot RAG retrieval on Joe Lotito transcript"""
    print("=" * 80)
    print("RAG TEST - Joe Lotito Transcript")
    print("=" * 80)

    agent = SalesCopilotAgent(settings)

    # Test query about Joe Lotito
    query = "What were Joe Lotito's estate planning needs and concerns?"
    transcript_id = "58051552"  # Joe Lotito's transcript ID

    print(f"\n📋 Query: {query}")
    print(f"📄 Transcript ID: {transcript_id}")
    print(f"\n🔍 Testing RAG retrieval...\n")

    # Call the agent with transcript scoping
    result = await agent.run(data={
        "query": query,
        "transcript_id": transcript_id
    })

    print("\n" + "=" * 80)
    print("RESULT:")
    print("=" * 80)

    response = result.get('response', {})
    if 'results' in response:
        results = response['results']
        print(f"\n✅ Retrieved {len(results)} chunks\n")

        # Show first 2 chunks
        for i, chunk in enumerate(results[:2], 1):
            text = chunk.get('text', '')[:300]
            print(f"Chunk {i}:")
            print(f"{text}...")
            print()
    else:
        print(result)

    return result

if __name__ == "__main__":
    asyncio.run(test_rag())
