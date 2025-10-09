#!/usr/bin/env python3
"""
Test optimized pipeline with a REAL transcript (no test files).
Uses Sylvia Flynn transcript for verification.
"""
import asyncio
import time
from pathlib import Path
from orchestrator.pipeline import run_pipeline
from config.settings import settings

async def main():
    # Use Sylvia Flynn transcript - known good transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Deepak Naik: Estate Planning Advisor Meeting.txt")

    if not transcript_path.exists():
        print(f"❌ Transcript not found: {transcript_path}")
        return

    print("="*80)
    print("🧪 TESTING OPTIMIZED PIPELINE (NO KNOWLEDGEANALYST)")
    print("="*80)
    print(f"Transcript: {transcript_path.name}")
    print("="*80 + "\n")

    start_time = time.time()
    final_state = await run_pipeline(transcript_path)
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("⏱️  RESULTS")
    print("="*80)
    print(f"Time: {elapsed_time:.1f}s ({elapsed_time/60:.2f} min)")

    if final_state:
        print(f"✅ Transcript ID: {final_state.get('transcript_id')}")
        if final_state.get('crm_data'):
            crm = final_state['crm_data']
            print(f"✅ Client Name: {crm.get('client_name')}")
            print(f"✅ Client Email: {crm.get('client_email')}")
            print(f"✅ Marital Status: {crm.get('marital_status')}")
        print(f"✅ Persistence: {final_state.get('persistence_status')}")
    else:
        print("❌ No final_state returned")

if __name__ == "__main__":
    asyncio.run(main())
