"""
Direct test of Baserow integration (without running full pipeline)
"""
from config.settings import settings
from core.database.baserow import BaserowManager
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


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
        print(
            f"   - Communications table ID: {baserow_manager.communications_table_id}")
        print(
            f"   - Sales Coaching table ID: {baserow_manager.sales_coaching_table_id}")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    # Create mock CRM data - NEW TEST with different data
    print("\n2️⃣ Creating mock CRM data...")

    # Generate a new unique transcript ID for this test
    import random
    transcript_id = str(random.randint(80000000, 89999999))

    mock_crm_data = {
        "client_name": "Michael and Sarah Chen",
        "client_email": "mchen@techcorp.com",
        "customer_name": "Michael and Sarah Chen",  # Fallback field
        "marital_status": "Married",
        "children_count": 3,
        "estate_value": 850000,
        "real_estate_count": 2,
        "llc_interest": "Real estate investment LLC",
        "meeting_date": "2025-10-08",
        "transcript_filename": "test_new_client_2025_10_08.txt",
        "transcript_summary": "Second meeting to review Sub-trust options and LLC formation for real estate holdings. Clients very interested in asset protection strategies.",
        "outcome": "Won",
        "product_discussed": "Estate Planning, Trust Services, LLC Formation",
        "deal": 22500,
        "deposit": 7500,
        "objections_raised": "Questions about timing for LLC setup",
        "action_items": "Send LLC formation documents; Schedule closing call for next week",
        "follow_up_email_draft": "Dear Michael and Sarah, It was great meeting with you today to discuss your estate protection needs...",
        "email_draft": "Dear Michael and Sarah, It was great meeting with you today to discuss your estate protection needs...",
        "social_media_quote": "Protecting your family's future starts with the right planning today.",
        "coaching_opportunities": "Excellent presentation of Sub-trust benefits; Successfully addressed timing concerns with concrete next steps"
    }

    print(f"   ✅ Mock data created for NEW transcript ID: {transcript_id}")
    print(f"   📋 Client: Michael and Sarah Chen")
    print(f"   💰 Deal Amount: ${mock_crm_data['deal']}")

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
            print(
                f"   Look for data in all 5 tables with external_id = {result.get('external_id')}")
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
