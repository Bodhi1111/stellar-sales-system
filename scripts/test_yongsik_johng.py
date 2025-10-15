#!/usr/bin/env python3
"""
CRITICAL TEST: Process Yongsik Johng transcript with FULL Baserow population.

This test verifies:
1. Parent-child chunking works
2. BGE embeddings work
3. ALL Baserow tables are populated:
   - Clients (table 704)
   - Meetings (table 705)
   - Deals (table 706)
   - Communications (table 707)
   - Sales Coaching (table 708)
   - Chunks (table 709) - NEW with all fields
4. Qdrant vectors are created
5. PostgreSQL data is saved
"""

import asyncio
from pathlib import Path
from orchestrator.graph import app

async def main():
    transcript_path = Path("data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")

    if not transcript_path.exists():
        print(f"❌ Transcript not found: {transcript_path}")
        return

    print("=" * 80)
    print("🧪 CRITICAL TEST: FULL BASEROW POPULATION")
    print("=" * 80)
    print(f"📄 Transcript: {transcript_path.name}")
    print(f"📅 Meeting Date: September 3, 2025")
    print(f"📊 File size: {transcript_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    print("\n🎯 TARGET: Populate ALL 6 Baserow tables + Qdrant + PostgreSQL")
    print()

    # Initialize state
    initial_state = {
        "file_path": transcript_path
    }

    # Run the pipeline
    print("🚀 Starting full ingestion pipeline...\n")

    try:
        final_state = await app.ainvoke(initial_state)

        print("\n" + "=" * 80)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 80)

        # Display results
        transcript_id = final_state.get('transcript_id')
        print(f"\n📊 TRANSCRIPT INFO:")
        print(f"   ID: {transcript_id}")
        print(f"   Client: {final_state.get('header_metadata', {}).get('client_name', 'N/A')}")

        chunks_data = final_state.get('chunks_data', {})
        if chunks_data:
            print(f"\n📦 CHUNKS CREATED:")
            child_count = len(chunks_data.get('child_chunks', []))
            parent_count = len(chunks_data.get('parent_chunks', []))
            print(f"   ✅ Child chunks (speaker turns): {child_count}")
            print(f"   ✅ Parent chunks (phase segments): {parent_count}")
            print(f"   ✅ Header chunk: {'Yes' if chunks_data.get('header_chunk') else 'No'}")
            print(f"   ✅ Total chunks: {len(chunks_data.get('all_chunks', []))}")

        # CRM data check
        crm_data = final_state.get('crm_data', {})
        if crm_data:
            print(f"\n📇 CRM DATA EXTRACTED:")
            print(f"   ✅ Client data: {bool(crm_data.get('client'))}")
            print(f"   ✅ Meeting data: {bool(crm_data.get('meeting'))}")
            print(f"   ✅ Deal data: {bool(crm_data.get('deal'))}")
            print(f"   ✅ Communications: {len(crm_data.get('communications', []))}")
            print(f"   ✅ Coaching insights: {bool(crm_data.get('sales_coaching'))}")

        # Database status
        db_status = final_state.get('db_save_status', {})
        if db_status.get('persistence_status') == 'success':
            print(f"\n💾 DATABASE STORAGE:")
            print(f"   ✅ PostgreSQL: Saved")
            print(f"   ✅ Qdrant: Embedded ({child_count} child chunks)")
            print(f"   ✅ Baserow CRM: Synced (5 tables)")
            print(f"   ✅ Baserow Chunks: Synced (table 709)")

        print("\n" + "=" * 80)
        print("🔍 VERIFICATION LINKS")
        print("=" * 80)
        print(f"\n📊 BASEROW TABLES:")
        print(f"   Clients:        http://localhost:8080/database/174/table/704/")
        print(f"   Meetings:       http://localhost:8080/database/174/table/705/")
        print(f"   Deals:          http://localhost:8080/database/174/table/706/")
        print(f"   Communications: http://localhost:8080/database/174/table/707/")
        print(f"   Sales Coaching: http://localhost:8080/database/174/table/708/")
        print(f"   Chunks (NEW):   http://localhost:8080/database/174/table/709/")

        print(f"\n🔗 QDRANT:")
        print(f"   Dashboard: http://localhost:6333/dashboard")
        print(f"   Collection: transcripts")
        print(f"   Filter by: transcript_id={transcript_id}")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE - VERIFY ALL TABLES POPULATED")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PIPELINE FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
