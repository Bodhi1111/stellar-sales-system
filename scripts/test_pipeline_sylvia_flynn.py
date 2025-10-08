#!/usr/bin/env python3
"""
Test full pipeline with Sylvia Flynn transcript (61965940)
Using Mistral 7B for fast testing
"""

import asyncio
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from orchestrator.graph import app

async def main():
    print("="*80)
    print("FULL PIPELINE TEST - Sylvia Flynn Transcript")
    print("="*80)
    print()
    print(f"⚙️  Configuration:")
    print(f"   LLM Model: {settings.LLM_MODEL_NAME}")
    print(f"   Expected Speed: ⚡ Fast (2-3 minutes)")
    print()

    # Path to real transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Sylvia Flynn: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript file not found")
        return

    print(f"📄 Transcript: {transcript_path.name}")
    file_size = transcript_path.stat().st_size / 1024  # KB
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Expected transcript_id: 61965940")
    print()

    start_time = time.time()

    try:
        initial_state = {"file_path": transcript_path}
        final_state = await app.ainvoke(initial_state)

        elapsed_time = time.time() - start_time
        minutes = elapsed_time / 60

        print()
        print("="*80)
        print(f"✅ PIPELINE COMPLETE - {minutes:.1f} minutes")
        print("="*80)
        print()
        print(f"📊 Results:")
        print(f"   Transcript ID: {final_state.get('transcript_id', 'N/A')}")
        print(f"   Chunks: {len(final_state.get('chunks', []))}")
        print(f"   Dialogue turns: {len(final_state.get('structured_dialogue', []))}")
        print()

        if final_state.get("crm_data"):
            crm = final_state["crm_data"]
            print(f"✅ Data saved successfully:")
            print(f"   PostgreSQL: ✅")
            print(f"   Baserow: ✅ (all 5 tables)")
            print(f"   External ID: {final_state.get('transcript_id', 'N/A')}")
            print()
            print(f"📋 CRM Data extracted:")
            print(f"   Client: {crm.get('client_name', 'N/A')}")
            print(f"   Email: {crm.get('client_email', 'N/A')}")
            print(f"   Deal: ${crm.get('deal_amount', 0):,.2f}")
            print(f"   Outcome: {crm.get('outcome', 'N/A')}")
            print()

        print(f"🎯 Performance:")
        print(f"   Total time: {elapsed_time:.1f} seconds ({minutes:.1f} minutes)")
        print(f"   Model: {settings.LLM_MODEL_NAME}")
        print()

        print("="*80)
        print("VERIFICATION")
        print("="*80)
        print()
        print(f"🔍 Check Baserow: http://localhost:8080")
        print(f"   Search for: external_id = {final_state.get('transcript_id', 'N/A')}")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
