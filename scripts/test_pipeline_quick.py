"""
Quick pipeline test - Parser + Baserow only (skip heavy LLM processing)
Tests that the transcript is properly parsed and synced to Baserow
"""
from config.settings import settings
from core.database.baserow import BaserowManager
from agents.parser.parser_agent import ParserAgent
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_parse_and_sync():
    """Quick test: Parse transcript and sync to Baserow"""
    print("=" * 80)
    print("QUICK PIPELINE TEST - Parse + Baserow Sync")
    print("=" * 80)

    # Path to the real transcript
    transcript_path = Path(
        "/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/John and Janice Suss: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript file not found")
        return

    print(f"\n📄 Transcript: {transcript_path.name}")

    # Step 1: Parse the transcript
    print("\n1️⃣ Parsing transcript...")
    parser = ParserAgent(settings)
    parse_result = await parser.run(file_path=transcript_path)

    transcript_id = parse_result.get("transcript_id")
    dialogue = parse_result.get("structured_dialogue", [])

    print(f"   ✅ Parsed successfully")
    print(f"   Transcript ID: {transcript_id}")
    print(f"   Dialogue turns: {len(dialogue)}")

    if len(dialogue) > 0:
        first_turn = dialogue[0]
        print(f"   First speaker: {first_turn.get('speaker', 'N/A')}")

    # Step 2: Create mock CRM data from parsed info
    print("\n2️⃣ Creating CRM data from parsed transcript...")

    # Extract basic info from transcript
    client_name = "John and Janice Suss"
    client_email = "johnsuss007@gmail.com"

    mock_crm_data = {
        "client_name": client_name,
        "client_email": client_email,
        "customer_name": client_name,
        "marital_status": "Married",
        "children_count": 2,
        "estate_value": 0,  # Would be extracted by LLM in full pipeline
        "real_estate_count": 2,  # Minnesota cabin + Florida house
        "llc_interest": "None mentioned",
        "meeting_date": "2025-10-07",
        "transcript_filename": transcript_path.name,
        "transcript_summary": f"Estate planning consultation with {client_name}. Discussed trust setup for two properties (Minnesota and Florida), protection for beneficiaries, and nursing home asset protection.",
        "outcome": "Won",  # Client agreed to proceed ($3,425 package)
        "product_discussed": "Estate Planning, Revocable Living Trust, Asset Protection",
        "deal": 3425,  # Amount from transcript
        "deposit": 3425,
        "objections_raised": "Previous bad experience with financial advisor",
        "action_items": "Pre-meeting questionnaire; Client meeting scheduled for Oct 9th at 9am CT with Michael Simpson",
        "follow_up_email_draft": f"Dear {client_name}, Thank you for choosing our estate planning services. Your next meeting is scheduled with Michael Simpson...",
        "email_draft": f"Dear {client_name}, Thank you for choosing our estate planning services...",
        "social_media_quote": "Estate planning isn't just about assets—it's about protecting the people you love.",
        "coaching_opportunities": "Excellent rapport building; Successfully addressed client's concerns about previous advisor experience; Clear explanation of trust benefits"
    }

    print(f"   ✅ CRM data prepared")
    print(f"   Client: {client_name}")
    print(f"   Deal: ${mock_crm_data['deal']}")
    print(f"   Properties: {mock_crm_data['real_estate_count']}")

    # Step 3: Sync to Baserow
    print("\n3️⃣ Syncing to Baserow...")
    baserow_manager = BaserowManager(settings)

    sync_result = await baserow_manager.sync_crm_data(mock_crm_data, transcript_id)

    if sync_result.get("status") == "success":
        print(f"\n✅ BASEROW SYNC SUCCESSFUL!")
        print(f"   External ID: {sync_result.get('external_id')}")
    else:
        print(f"\n❌ Baserow sync failed: {sync_result.get('error')}")

    # Step 4: Verify in Baserow
    print("\n4️⃣ Verifying records in Baserow...")
    import requests

    headers = {"Authorization": f"Token {settings.BASEROW_TOKEN}"}

    # Check Clients table
    url = f"{settings.BASEROW_URL}/api/database/rows/table/{settings.BASEROW_CLIENTS_ID}/?user_field_names=true&filter__external_id__equal={transcript_id}"
    response = requests.get(url, headers=headers)
    data = response.json()

    if data['count'] == 1:
        record = data['results'][0]
        print(f"   ✅ Client record found:")
        print(f"      Row ID: {record['id']}")
        print(f"      Client: {record.get('client_name', 'N/A')}")
        print(f"      Email: {record.get('email', 'N/A')}")
        print(f"      Estate Value: ${record.get('estate_value', 0)}")
    else:
        print(f"   ⚠️ Expected 1 record, found {data['count']}")

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print(f"\n🌐 Check Baserow UI: http://localhost:8080")
    print(f"   Search for external_id: {transcript_id}")
    print(f"   Expected: Records in all 5 tables")
    print(f"   - Clients table (ID 704)")
    print(f"   - Meetings table (ID 705)")
    print(f"   - Deals table (ID 706)")
    print(f"   - Communications table (ID 707)")
    print(f"   - Sales Coaching table (ID 708)")

    print("\n" + "=" * 80)
    print("✅ QUICK TEST COMPLETE")
    print("=" * 80)
    print(f"\n💡 To run the full pipeline with all LLM agents:")
    print(f"   ./venv/bin/python scripts/test_pipeline_direct.py")
    print(f"   (Note: This takes 5-10 minutes due to DeepSeek 33B model)")


if __name__ == "__main__":
    asyncio.run(test_parse_and_sync())
