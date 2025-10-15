#!/usr/bin/env python3
"""
Test script to process Nelson Diaz transcript through parent-child chunking pipeline.
"""

import asyncio
from pathlib import Path
from orchestrator.graph import app

async def main():
    transcript_path = Path("data/transcripts/NELSON DIAZ: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ Transcript not found: {transcript_path}")
        return

    print("=" * 80)
    print("🧪 TESTING PARENT-CHILD CHUNKING ARCHITECTURE")
    print("=" * 80)
    print(f"📄 Processing: {transcript_path.name}")
    print(f"📊 File size: {transcript_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    print()

    # Initialize state
    initial_state = {
        "file_path": transcript_path
    }

    # Run the pipeline
    print("🚀 Starting ingestion pipeline with parent-child chunking...\n")

    try:
        final_state = await app.ainvoke(initial_state)

        print("\n" + "=" * 80)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)

        # Display results
        print(f"\n📊 RESULTS:")
        print(f"   Transcript ID: {final_state.get('transcript_id')}")

        chunks_data = final_state.get('chunks_data', {})
        if chunks_data:
            print(f"\n📦 CHUNKS CREATED:")
            print(f"   - Child chunks (speaker turns): {len(chunks_data.get('child_chunks', []))}")
            print(f"   - Parent chunks (phase segments): {len(chunks_data.get('parent_chunks', []))}")
            print(f"   - Header chunk: {'Yes' if chunks_data.get('header_chunk') else 'No'}")
            print(f"   - Total chunks: {len(chunks_data.get('all_chunks', []))}")

        # Show database status
        db_status = final_state.get('db_save_status', {})
        if db_status.get('persistence_status') == 'success':
            print(f"\n💾 DATABASE:")
            print(f"   - PostgreSQL: ✅ Saved")
            print(f"   - Baserow CRM: ✅ Synced")
            print(f"   - Baserow Chunks: ✅ Synced")
            print(f"   - Qdrant: ✅ Embedded")

        print("\n🔗 VERIFY IN BASEROW:")
        print(f"   - Chunks table: http://localhost:8080/database/174/table/709/")
        print(f"   - Clients table: http://localhost:8080/database/174/table/704/")

        print("\n🔗 VERIFY IN QDRANT:")
        print(f"   - Dashboard: http://localhost:6333/dashboard")
        print(f"   - Collection: transcripts")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
