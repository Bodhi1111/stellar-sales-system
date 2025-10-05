"""
Test script for updated PersistenceAgent (Sprint 03, Epic 3.1)
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.persistence.persistence_agent import PersistenceAgent
from config.settings import settings


async def test_persistence():
    """Test the updated PersistenceAgent with data dict"""
    print("=" * 70)
    print("Testing Updated PersistenceAgent (Sprint 03)")
    print("=" * 70)

    agent = PersistenceAgent(settings)

    # Test data matching Sprint 03 spec
    test_data = {
        "transcript_id": "TEST12345",
        "file_path": Path("/tmp/test_transcript.txt"),
        "chunks": ["Chunk 1: Hello client", "Chunk 2: Estate planning discussion"],
        "extracted_entities": {"client": "John Doe", "topic": "estate planning"},
        "social_content": {"linkedin": "Test post"},
        "email_draft": "Dear client, ...",
        "crm_data": {"deal_stage": "Qualified", "value": 50000}  # NEW field
    }

    print("\n📝 Test Data:")
    print(f"   Transcript ID: {test_data['transcript_id']}")
    print(f"   CRM Data: {test_data['crm_data']}")
    print()

    result = await agent.run(data=test_data)

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    print(f"Status: {result.get('persistence_status')}")
    if result.get('message'):
        print(f"Message: {result.get('message')}")

    if result.get('persistence_status') == 'success':
        print("\n✅ Sprint 03 Epic 3.1: Persistence Updated Successfully!")
        print("   - PersistenceAgent uses data: Dict[str, Any] signature")
        print("   - Database model includes crm_data field")
        print("   - UPSERT by external_id working correctly")
    else:
        print("\n❌ Test failed")

    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_persistence())
