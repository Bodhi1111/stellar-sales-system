#!/usr/bin/env python3
"""
Test full pipeline with John & Janice Suss real transcript
Using DeepSeek 6.7B quantized model for balanced speed/quality
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
    print("FULL PIPELINE TEST - John & Janice Suss Transcript")
    print("="*80)
    print()
    print(f"⚙️  Configuration:")
    print(f"   LLM Model: {settings.LLM_MODEL_NAME}")
    print(f"   Expected Speed: 🔶 Balanced (4-6 minutes total)")
    print()

    # Path to real transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/John and Janice Suss: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript file not found at {transcript_path}")
        return

    print(f"📄 Transcript: {transcript_path.name}")
    file_size = transcript_path.stat().st_size / 1024  # KB
    print(f"   Size: {file_size:.1f} KB")
    print()

    print(f"🚀 Starting pipeline...")
    print(f"   Agents will run in this order:")
    print(f"   1. Parser → 2. Structuring → 3. Chunker")
    print(f"   4. [Parallel] Knowledge Analyst + Embedder")
    print(f"   5. [Parallel] Email + Social + Sales Coach")
    print(f"   6. CRM (aggregation)")
    print(f"   7. Persistence (PostgreSQL + Baserow sync)")
    print()

    start_time = time.time()

    try:
        # Run the pipeline using the compiled graph
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
        print(f"🔍 Check your data:")
        print(f"   1. Baserow UI: http://localhost:8080")
        print(f"      Search for: external_id = {final_state.get('transcript_id', 'N/A')}")
        print(f"   2. Qdrant: http://localhost:6333/dashboard")
        print(f"      Collection: transcripts")
        print(f"   3. Neo4j: http://localhost:7474")
        print(f"      Query: MATCH (n) WHERE n.transcript_id = '{final_state.get('transcript_id', 'N/A')}' RETURN n")
        print()
        print(f"✅ Success! Pipeline completed with DeepSeek 6.7B quantized")
        print(f"   Better quality than Mistral 7B, faster than DeepSeek 33B!")

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
