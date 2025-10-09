#!/usr/bin/env python3
"""
Final test with all fixes applied:
1. Duplicate JSON schema removed
2. Mistral 7B (fast performance)
3. CRM field mapping fixed (client_name)
4. Baserow date handling fixed
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.pipeline import run_pipeline


async def test_final():
    print("=" * 80)
    print("FINAL TEST - All Fixes Applied (Mistral 7B)")
    print("=" * 80)

    # Allan May transcript - fresh, untouched
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Allan May: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ Transcript not found")
        return 1

    print(f"\n📄 Transcript: {transcript_path.name}")
    print(f"📊 Size: {transcript_path.stat().st_size / 1024:.1f} KB")
    print(f"\n🔧 Fixes Applied:")
    print(f"   ✅ Duplicate JSON schema removed")
    print(f"   ✅ LLM: Mistral 7B (fast)")
    print(f"   ✅ CRM client_name field mapping fixed")
    print(f"   ✅ Baserow date handling fixed (exclude empty)")

    print(f"\n🚀 Running complete pipeline...")
    print("-" * 80)

    try:
        # Run pipeline
        final_state = await run_pipeline(file_path=transcript_path)

        if not final_state:
            print(f"\n❌ Pipeline returned None")
            return 1

        # Extract results
        transcript_id = final_state.get('transcript_id')
        extracted = final_state.get('extracted_entities', {})
        crm_data = final_state.get('crm_data', {})
        db_status = final_state.get('db_save_status', {})

        print(f"\n" + "=" * 80)
        print(f"RESULTS")
        print(f"=" * 80)

        print(f"\n📊 Extraction:")
        print(f"   Transcript ID: {transcript_id}")
        print(f"   Client Name: {extracted.get('client_name', 'NOT EXTRACTED')}")
        print(f"   Email: {extracted.get('client_email', 'NOT EXTRACTED')}")
        print(f"   Meeting Date: {extracted.get('meeting_date', 'NOT EXTRACTED')}")
        print(f"   Marital Status: {extracted.get('marital_status', 'NOT EXTRACTED')}")

        print(f"\n💼 CRM Data:")
        print(f"   CRM Client Name: {crm_data.get('client_name', 'EMPTY')}")
        print(f"   CRM Email: {crm_data.get('client_email', 'EMPTY')}")

        print(f"\n💾 Database:")
        print(f"   PostgreSQL: {db_status.get('persistence_status', 'unknown')}")

        # Verify in Baserow
        import requests
        response = requests.get(
            f"http://localhost:8080/api/database/rows/table/704/?user_field_names=true&filter__external_id__equal={transcript_id}",
            headers={"Authorization": "Token 6TElBEHaafiG4nmajttcnaN7TZEIioi7"}
        )

        if response.ok:
            data = response.json()
            if data['count'] > 0:
                client = data['results'][0]
                print(f"\n✅ BASEROW VERIFICATION:")
                print(f"   Client Name: '{client.get('client_name')}'")
                print(f"   Email: {client.get('email')}")
                print(f"   External ID: {client.get('external_id')}")

                # Check if client_name is populated
                if client.get('client_name') and client.get('client_name').strip():
                    print(f"\n🎉 SUCCESS! Client name is populated in Baserow!")
                    return 0
                else:
                    print(f"\n❌ FAIL: Client name still empty in Baserow")
                    return 1
            else:
                print(f"\n⚠️  No Baserow record found")
                return 1
        else:
            print(f"\n❌ Baserow query failed: {response.status_code}")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_final())
    sys.exit(exit_code)
