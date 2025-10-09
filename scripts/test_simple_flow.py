#!/usr/bin/env python3
"""
Simple test to debug KnowledgeAnalyst bottleneck.
Test just the KnowledgeAnalyst agent with minimal data.
"""
import asyncio
from pathlib import Path
from config.settings import settings
from agents.knowledge_analyst.knowledge_analyst_agent import KnowledgeAnalystAgent

async def main():
    print("="*80)
    print("TESTING SIMPLIFIED KNOWLEDGEANALYST")
    print("="*80)

    agent = KnowledgeAnalystAgent(settings)

    # Test with no CRM data (should use fast header fallback)
    file_path = Path("data/transcripts/test_file.txt")
    transcript_id = "test123"

    print("\n🔍 Test 1: No CRM data (should use fast header fallback)")
    result = await agent.run(
        transcript_id=transcript_id,
        file_path=file_path,
        crm_data=None  # No CRM data
    )
    print(f"Result: {result}")

    print("\n🔍 Test 2: With CRM data (should skip extraction)")
    crm_data = {
        "client_name": "Test Client",
        "client_email": "test@example.com",
        "marital_status": "Married",
        "children_count": 2,
        "outcome": "Won",
        "objections_raised": "Price too high",
        "product_discussed": "Estate Planning"
    }
    result2 = await agent.run(
        transcript_id=transcript_id,
        file_path=file_path,
        crm_data=crm_data
    )
    print(f"Result: {result2}")

    print("\n" + "="*80)
    print("✅ TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
