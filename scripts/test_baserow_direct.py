"""
Direct test of Baserow integration (without running full pipeline)
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.baserow import BaserowManager
from config.settings import settings


async def test_baserow_direct():
    """Test Baserow sync with mock CRM data"""
    print("=" * 70)
    print("Testing Baserow Direct Integration")
    print("=" * 70)

    # Create BaserowManager
    print("\n1️⃣ Initializing BaserowManager...")
    try:
        baserow_manager = BaserowManager(settings)
        print("   ✅ BaserowManager initialized")
        print(f"   - Clients table ID: {baserow_manager.clients_table_id}")
        print(f"   - Meetings table ID: {baserow_manager.meetings_table_id}")
        print(f"   - Deals table ID: {baserow_manager.deals_table_id}")
        print(f"   - Communications table ID: {baserow_manager.communications_table_id}")
        print(f"   - Sales Coaching table ID: {baserow_manager.sales_coaching_table_id}")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    # Create mock CRM data
    print("\n2️⃣ Creating mock CRM data...")
    mock_crm_data = {
        "client_name": "John and Jane Doe",
        "client_email": "johndoe@example.com",
        "customer_name": "John and Jane Doe",  # Fallback field
        "marital_status": "Married",
        "children_count": 2,
        "estate_value": 500000,
        "real_estate_count": 1,
        "llc_interest": "Tech startup LLC",
        "meeting_date": "2025-10-07",
        "transcript_filename": "test_baserow_direct.txt",
        "transcript_summary": "Initial estate planning consultation discussing trust setup and life insurance options.",
        "outcome": "Follow-up Scheduled",
        "product_discussed": "Estate Planning, Trust Services",
        "deal": 15000,
        "deposit": 5000,
        "objections_raised": "Concerns about pricing and timeline",
        "action_items": "Schedule follow-up call; Send trust setup documentation",
        "follow_up_email_draft": "Dear John and Jane, Thank you for meeting with me today...",
        "email_draft": "Dear John and Jane, Thank you for meeting with me today...",
        "social_media_quote": "Estate planning isn't just about assets—it's about protecting the people you love.",
        "coaching_opportunities": "Strong rapport building; Could improve objection handling around pricing"
    }

    transcript_id = "62022857"  # Test transcript ID
    print(f"   ✅ Mock data created for transcript ID: {transcript_id}")

    # Test Baserow sync
    print("\n3️⃣ Syncing to Baserow...")
    try:
        result = await baserow_manager.sync_crm_data(mock_crm_data, transcript_id)

        print("\n" + "=" * 70)
        print("SYNC RESULT")
        print("=" * 70)

        if result.get("status") == "success":
            print("✅ Baserow sync successful!")
            print(f"   - External ID: {result.get('external_id')}")
            print(f"\n📊 Check Baserow UI: http://localhost:8080")
            print(f"   Look for data in all 5 tables with external_id = {result.get('external_id')}")
        else:
            print("❌ Baserow sync failed")
            print(f"   Error: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ ERROR during sync: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_baserow_direct())
