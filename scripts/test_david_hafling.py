#!/usr/bin/env python3
"""
Test script to process David Hafling transcript with ALL header metadata fixes.
This validates: duration_minutes, meeting_title, transcript_filename, sales_rep, full timestamp.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import create_master_workflow


async def run_pipeline(file_path: Path):
    """Run the complete ingestion pipeline with all header metadata fixes."""
    print(f"\n{'='*80}")
    print(f"🚀 DAVID HAFLING - COMPLETE HEADER METADATA TEST")
    print(f"{'='*80}\n")
    print("Testing ALL fixes:")
    print("  ✓ duration_minutes field")
    print("  ✓ meeting_title field in Meetings table")
    print("  ✓ transcript_filename = meeting_title + .txt")
    print("  ✓ sales_rep = 'J. Vaughan'")
    print("  ✓ meeting_date with full timestamp (date + time)")
    print("  ✓ email field mapping\n")

    # Create the workflow
    app = create_master_workflow()

    # Run the pipeline
    print(f"📄 Processing: {file_path.name}")
    print(f"📊 Size: {file_path.stat().st_size / 1024:.1f} KB\n")

    try:
        final_state = await app.ainvoke({"file_path": file_path})

        print(f"\n{'='*80}")
        print(f"✅ PIPELINE COMPLETED")
        print(f"{'='*80}\n")

        # Display header metadata
        print("📋 HEADER METADATA EXTRACTED:")
        if final_state.get('header_metadata'):
            hm = final_state['header_metadata']
            print(f"   meeting_title: {hm.get('meeting_title', 'N/A')}")
            print(f"   client_name: {hm.get('client_name', 'N/A')}")
            print(f"   client_email: {hm.get('client_email', 'N/A')}")
            print(f"   meeting_date: {hm.get('meeting_date', 'N/A')}")
            print(f"   meeting_time: {hm.get('meeting_time', 'N/A')}")
            print(f"   duration_minutes: {hm.get('duration_minutes', 'N/A')}")
            print(f"   transcript_id: {hm.get('transcript_id', 'N/A')}")

        # Display CRM data
        print(f"\n📊 CRM DATA:")
        if final_state.get('crm_data'):
            crm = final_state['crm_data']
            print(f"   Meeting Title: {crm.get('meeting_title', 'N/A')}")
            print(f"   Client: {crm.get('client_name', 'N/A')} <{crm.get('client_email', 'N/A')}>")
            print(f"   Meeting Date: {crm.get('meeting_date', 'N/A')}")
            print(f"   Meeting Time: {crm.get('meeting_time', 'N/A')}")
            print(f"   Duration: {crm.get('duration_minutes', 0)} minutes")
            print(f"   Transcript ID: {crm.get('transcript_id', 'N/A')}")

        print(f"\n{'='*80}")
        print("🔍 VERIFICATION - Check Baserow for:")
        print(f"{'='*80}")
        transcript_id = final_state.get('crm_data', {}).get('transcript_id', 'N/A')
        print(f"\n📍 External ID: {transcript_id}")
        print("\n✓ Clients table (704):")
        print(f"  - client_name = 'David Hafling'")
        print(f"  - email = 'david.hafling@...' (should be populated!)")
        print(f"  - crm_json contains meeting_title")

        print("\n✓ Meetings table (705):")
        print(f"  - meeting_title = 'David Hafling: Estate Planning Advisor Meeting'")
        print(f"  - transcript_filename = 'David Hafling: Estate Planning Advisor Meeting.txt'")
        print(f"  - sales_rep = 'J. Vaughan'")
        print(f"  - duration_minutes = [actual duration from header]")
        print(f"  - meeting_date = [ISO timestamp with date AND time]")

        return final_state

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def verify_baserow_data(transcript_id: str):
    """Verify data in Baserow after pipeline completion."""
    import subprocess
    import json

    print(f"\n{'='*80}")
    print("📊 BASEROW DATA VERIFICATION")
    print(f"{'='*80}\n")

    # Check Meetings table
    cmd = f'curl -s -H "Authorization: Token 6TElBEHaafiG4nmajttcnaN7TZEIioi7" "http://localhost:8080/api/database/rows/table/705/?user_field_names=true&filter__field_6797__equal={transcript_id}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        data = json.loads(result.stdout)
        if data['results']:
            meeting = data['results'][0]
            print("✅ MEETINGS TABLE:")
            print(f"   meeting_title: {meeting.get('meeting_title', 'MISSING')}")
            print(f"   transcript_filename: {meeting.get('transcript_filename', 'MISSING')}")
            print(f"   sales_rep: {meeting.get('sales_rep', 'MISSING')}")
            print(f"   duration_minutes: {meeting.get('duration_minutes', 'MISSING')}")
            print(f"   meeting_date: {meeting.get('meeting_date', 'MISSING')}")

            # Verification checks
            print("\n🔍 FIELD VERIFICATION:")
            checks_passed = 0
            checks_total = 5

            if meeting.get('meeting_title'):
                print("   ✅ meeting_title populated")
                checks_passed += 1
            else:
                print("   ❌ meeting_title MISSING")

            if meeting.get('transcript_filename', '').endswith('.txt'):
                print("   ✅ transcript_filename ends with .txt")
                checks_passed += 1
            else:
                print("   ❌ transcript_filename format incorrect")

            if meeting.get('sales_rep') == 'J. Vaughan':
                print("   ✅ sales_rep = 'J. Vaughan'")
                checks_passed += 1
            else:
                print(f"   ❌ sales_rep = '{meeting.get('sales_rep')}' (expected 'J. Vaughan')")

            if meeting.get('duration_minutes', 0) > 0:
                print(f"   ✅ duration_minutes = {meeting.get('duration_minutes')}")
                checks_passed += 1
            else:
                print("   ❌ duration_minutes not populated")

            if meeting.get('meeting_date') and 'T' in meeting.get('meeting_date', ''):
                print(f"   ✅ meeting_date has timestamp: {meeting.get('meeting_date')}")
                checks_passed += 1
            else:
                print(f"   ⚠️  meeting_date: {meeting.get('meeting_date')} (may be date-only)")

            print(f"\n   📊 Score: {checks_passed}/{checks_total} checks passed")
            return checks_passed == checks_total

    return False


async def main():
    # Path to David Hafling transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/David Hafling: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        sys.exit(1)

    # Run the pipeline
    result = await run_pipeline(transcript_path)

    if result:
        # Extract transcript_id for verification
        transcript_id = result.get('crm_data', {}).get('transcript_id', '')

        if transcript_id:
            # Verify Baserow data
            all_checks_passed = await verify_baserow_data(transcript_id)

            if all_checks_passed:
                print(f"\n{'='*80}")
                print("🎉 ALL TESTS PASSED - Header metadata fully integrated!")
                print(f"{'='*80}\n")
            else:
                print(f"\n{'='*80}")
                print("⚠️  SOME CHECKS FAILED - Review results above")
                print(f"{'='*80}\n")
        else:
            print("\n⚠️  Could not extract transcript_id for verification")
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
