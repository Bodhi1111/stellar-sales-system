"""
Comprehensive test of Baserow UPSERT behavior
Tests both CREATE (new external_id) and UPDATE (existing external_id) paths
"""
from config.settings import settings
from core.database.baserow import BaserowManager
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_baserow_upsert():
    """Test complete upsert behavior: CREATE then UPDATE same record"""
    print("=" * 70)
    print("BASEROW UPSERT VALIDATION TEST")
    print("=" * 70)

    baserow_manager = BaserowManager(settings)

    # Use a fixed transcript ID for this test
    test_transcript_id = "99000001"

    # ===================================================================
    # TEST 1: CREATE - First insert with this external_id
    # ===================================================================
    print("\n" + "=" * 70)
    print("TEST 1: CREATE NEW RECORD")
    print("=" * 70)

    mock_crm_data_v1 = {
        "client_name": "Test Client - Version 1",
        "client_email": "test.v1@example.com",
        "customer_name": "Test Client - Version 1",
        "marital_status": "Single",
        "children_count": 1,
        "estate_value": 100000,
        "real_estate_count": 1,
        "llc_interest": "None",
        "meeting_date": "2025-10-08",
        "transcript_filename": "test_upsert_v1.txt",
        "transcript_summary": "Initial consultation - Version 1",
        "outcome": "Pending",
        "product_discussed": "Estate Planning",
        "deal": 5000,
        "deposit": 1000,
        "objections_raised": "Price concerns",
        "action_items": "Follow up next week",
        "follow_up_email_draft": "Dear Client, Version 1...",
        "email_draft": "Dear Client, Version 1...",
        "social_media_quote": "Version 1 quote",
        "coaching_opportunities": "Version 1 coaching"
    }

    print(f"\n📝 Creating record with external_id: {test_transcript_id}")
    print(f"   Client name: {mock_crm_data_v1['client_name']}")
    print(f"   Deal amount: ${mock_crm_data_v1['deal']}")

    result1 = await baserow_manager.sync_crm_data(mock_crm_data_v1, test_transcript_id)

    if result1.get("status") == "success":
        print(f"\n✅ CREATE successful!")
        print(f"   External ID: {result1.get('external_id')}")
    else:
        print(f"\n❌ CREATE failed: {result1.get('error')}")
        return

    # ===================================================================
    # TEST 2: UPDATE - Second insert with SAME external_id
    # ===================================================================
    print("\n" + "=" * 70)
    print("TEST 2: UPDATE EXISTING RECORD")
    print("=" * 70)

    mock_crm_data_v2 = {
        "client_name": "Test Client - Version 2 UPDATED",
        "client_email": "test.v2@example.com",
        "customer_name": "Test Client - Version 2 UPDATED",
        "marital_status": "Married",
        "children_count": 3,
        "estate_value": 500000,
        "real_estate_count": 2,
        "llc_interest": "Tech LLC",
        "meeting_date": "2025-10-09",
        "transcript_filename": "test_upsert_v2.txt",
        "transcript_summary": "Follow-up meeting - Version 2 UPDATED",
        "outcome": "Won",
        "product_discussed": "Estate Planning, Trust Services",
        "deal": 15000,
        "deposit": 5000,
        "objections_raised": "None",
        "action_items": "Send contract",
        "follow_up_email_draft": "Dear Client, Version 2 UPDATED...",
        "email_draft": "Dear Client, Version 2 UPDATED...",
        "social_media_quote": "Version 2 quote UPDATED",
        "coaching_opportunities": "Version 2 coaching UPDATED"
    }

    print(f"\n📝 Updating record with SAME external_id: {test_transcript_id}")
    print(f"   Client name: {mock_crm_data_v2['client_name']}")
    print(f"   Deal amount: ${mock_crm_data_v2['deal']}")

    result2 = await baserow_manager.sync_crm_data(mock_crm_data_v2, test_transcript_id)

    if result2.get("status") == "success":
        print(f"\n✅ UPDATE successful!")
        print(f"   External ID: {result2.get('external_id')}")
    else:
        print(f"\n❌ UPDATE failed: {result2.get('error')}")
        return

    # ===================================================================
    # VALIDATION: Query Baserow to verify behavior
    # ===================================================================
    print("\n" + "=" * 70)
    print("VALIDATION: Verify Database State")
    print("=" * 70)

    import requests
    headers = {"Authorization": f"Token {settings.BASEROW_TOKEN}"}
    url = f"{settings.BASEROW_URL}/api/database/rows/table/{settings.BASEROW_CLIENTS_ID}/?user_field_names=true&filter__external_id__equal={test_transcript_id}"
    response = requests.get(url, headers=headers)
    data = response.json()

    print(
        f"\n📊 Records with external_id={test_transcript_id}: {data['count']}")
    print(f"   Expected: 1 (same record updated, not duplicated)")

    if data['count'] == 1:
        record = data['results'][0]
        print(f"\n✅ PASS: Only 1 record exists (correct upsert behavior)")
        print(f"   Row ID: {record['id']}")
        print(f"   Client name: {record['client_name']}")
        print(f"   Estate value: ${record['estate_value']}")
        print(f"   Children: {record['children_count']}")

        # Verify it has the UPDATED data (Version 2)
        if record['client_name'] == "Test Client - Version 2 UPDATED":
            print(f"\n✅ PASS: Record contains Version 2 data (correctly updated)")
        else:
            print(f"\n❌ FAIL: Record still has old data")

        if int(record['estate_value']) == 500000:
            print(f"✅ PASS: Estate value updated correctly (500000)")
        else:
            print(
                f"❌ FAIL: Estate value not updated (expected 500000, got {record['estate_value']})")

    elif data['count'] == 2:
        print(f"\n❌ FAIL: 2 records exist (duplicate created instead of update)")
        print(f"   This means upsert is not working correctly")
    else:
        print(f"\n⚠️ Unexpected result: {data['count']} records")

    print("\n" + "=" * 70)
    print("UPSERT TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_baserow_upsert())
