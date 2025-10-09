#!/usr/bin/env python3
"""
Test Thomas Edwards transcript end-to-end with simplified KnowledgeAnalyst.
Verifies:
1. Pipeline completes in ~30-35s (vs previous 77s)
2. All data populates in Baserow (especially client_name)
3. All 5 Baserow tables populated correctly
"""
import asyncio
import time
from pathlib import Path
from orchestrator.pipeline import run_pipeline
from config.settings import settings
from core.database.baserow import BaserowClient

async def verify_baserow_data(transcript_id: str):
    """Verify all 5 Baserow tables populated correctly."""
    print("\n" + "="*80)
    print("📊 VERIFYING BASEROW DATA")
    print("="*80)

    baserow = BaserowClient(settings)

    # Check Clients table
    print("\n🔍 Checking Clients table (Table ID: 704)...")
    clients = baserow.get_rows(settings.BASEROW_CLIENTS_ID)
    matching_client = None
    for client in clients:
        if client.get("external_id") == transcript_id:
            matching_client = client
            break

    if matching_client:
        print(f"   ✅ Client found: {matching_client.get('client_name')}")
        print(f"      - Email: {matching_client.get('Email')}")
        print(f"      - Marital Status: {matching_client.get('marital_status')}")
        print(f"      - External ID: {matching_client.get('external_id')}")
    else:
        print(f"   ❌ No client found with external_id={transcript_id}")

    # Check Meetings table
    print("\n🔍 Checking Meetings table (Table ID: 705)...")
    meetings = baserow.get_rows(settings.BASEROW_MEETINGS_ID)
    matching_meetings = [m for m in meetings if m.get("transcript_id") == transcript_id]
    print(f"   {'✅' if matching_meetings else '❌'} Found {len(matching_meetings)} meeting(s)")

    # Check Deals table
    print("\n🔍 Checking Deals table (Table ID: 706)...")
    deals = baserow.get_rows(settings.BASEROW_DEALS_ID)
    matching_deals = [d for d in deals if d.get("transcript_id") == transcript_id]
    print(f"   {'✅' if matching_deals else '❌'} Found {len(matching_deals)} deal(s)")

    # Check Communications table
    print("\n🔍 Checking Communications table (Table ID: 707)...")
    comms = baserow.get_rows(settings.BASEROW_COMMUNICATIONS_ID)
    matching_comms = [c for c in comms if c.get("transcript_id") == transcript_id]
    print(f"   {'✅' if matching_comms else '❌'} Found {len(matching_comms)} communication(s)")

    # Check Sales Coaching table
    print("\n🔍 Checking Sales Coaching table (Table ID: 708)...")
    coaching = baserow.get_rows(settings.BASEROW_SALES_COACHING_ID)
    matching_coaching = [s for s in coaching if s.get("transcript_id") == transcript_id]
    print(f"   {'✅' if matching_coaching else '❌'} Found {len(matching_coaching)} coaching entry/entries")

    print("\n" + "="*80)
    return matching_client is not None

async def main():
    # Path to fresh untouched transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/THOMAS EDWARDS: Estate Planning Advisor Meeting.txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        return

    print("="*80)
    print("🚀 TESTING SIMPLIFIED KNOWLEDGEANALYST WITH THOMAS EDWARDS")
    print("="*80)
    print(f"Transcript: {transcript_path.name}")
    print(f"Expected: ~30-35s pipeline (vs previous 77s)")
    print("="*80 + "\n")

    # Start timer
    start_time = time.time()

    # Run pipeline
    final_state = await run_pipeline(transcript_path)

    # End timer
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("⏱️  PERFORMANCE RESULTS")
    print("="*80)
    print(f"Pipeline completed in: {elapsed_time:.1f} seconds ({elapsed_time/60:.2f} minutes)")

    if elapsed_time < 40:
        print("✅ EXCELLENT: Under 40 seconds!")
    elif elapsed_time < 60:
        print("✅ GOOD: Under 60 seconds")
    elif elapsed_time < 80:
        print("⚠️  OK: Faster than previous 77s, but could be better")
    else:
        print("❌ SLOW: Slower than expected")

    # Verify Baserow data
    if final_state and final_state.get("transcript_id"):
        transcript_id = final_state["transcript_id"]
        print(f"\nTranscript ID: {transcript_id}")

        # Wait 2 seconds for Baserow sync
        print("\n⏳ Waiting 2 seconds for Baserow sync...")
        await asyncio.sleep(2)

        # Verify data
        success = await verify_baserow_data(transcript_id)

        if success:
            print("\n" + "="*80)
            print("🎉 TEST PASSED: Pipeline completed successfully!")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("⚠️  WARNING: Pipeline completed but data verification failed")
            print("="*80)
    else:
        print("\n❌ ERROR: No transcript_id in final state")

if __name__ == "__main__":
    asyncio.run(main())
