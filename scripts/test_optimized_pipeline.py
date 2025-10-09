#!/usr/bin/env python3
"""
Test optimized pipeline (no KnowledgeAnalyst bottleneck).
Verifies speed improvement and Baserow population.
"""
import asyncio
import time
from pathlib import Path
from orchestrator.pipeline import run_pipeline
from config.settings import settings
from core.database.baserow import BaserowClient

async def main():
    test_file = Path("data/transcripts/test_file.txt")

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return

    print("="*80)
    print("🚀 TESTING OPTIMIZED PIPELINE (NO KNOWLEDGEANALYST BOTTLENECK)")
    print("="*80)
    print(f"Test file: {test_file.name}")
    print("="*80 + "\n")

    start_time = time.time()
    final_state = await run_pipeline(test_file)
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("⏱️  PERFORMANCE RESULTS")
    print("="*80)
    print(f"Pipeline completed in: {elapsed_time:.1f} seconds ({elapsed_time/60:.2f} minutes)")

    if elapsed_time < 40:
        print("✅ EXCELLENT: Under 40 seconds! (vs 77s with KnowledgeAnalyst)")
    elif elapsed_time < 60:
        print("✅ GOOD: Under 60 seconds (vs 77s with KnowledgeAnalyst)")
    elif elapsed_time < 80:
        print("⚠️  OK: Faster than previous 77s, but could be better")
    else:
        print("❌ SLOW: Slower than expected")

    if final_state and final_state.get("transcript_id"):
        transcript_id = final_state["transcript_id"]
        print(f"\n✅ Transcript ID: {transcript_id}")
        print(f"✅ Pipeline status: SUCCESS")

        # Quick Baserow check
        print("\n🔍 Checking Baserow data...")
        baserow = BaserowClient(settings)
        clients = baserow.get_rows(settings.BASEROW_CLIENTS_ID)
        matching = [c for c in clients if str(c.get("external_id")) == str(transcript_id)]

        if matching:
            client = matching[0]
            print(f"   ✅ Client found: {client.get('client_name')}")
            print(f"   ✅ Email: {client.get('Email')}")
            print(f"   ✅ External ID: {client.get('external_id')}")
        else:
            print(f"   ⚠️  No client found with external_id={transcript_id}")
    else:
        print("\n❌ ERROR: No final_state or transcript_id")

    print("\n" + "="*80)
    print("🎉 TEST COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
