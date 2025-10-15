#!/usr/bin/env python3
"""
Process Joe Lotito transcript end-to-end: Parser → Chunking → Embedding → Baserow
"""
import asyncio
from pathlib import Path
from orchestrator.graph import app

async def main():
    transcript_path = Path("/Users/joshuavaughan/Documents/McAdams Transcripts/Joe Lotito: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ Transcript not found: {transcript_path}")
        return

    print("=" * 80)
    print("🧪 FULL PIPELINE TEST: JOE LOTITO")
    print("=" * 80)
    print(f"📄 Transcript: {transcript_path.name}")
    print(f"📊 File size: {transcript_path.stat().st_size / 1024:.1f} KB")
    print("=" * 80)
    print("\n🎯 TARGET: Process transcript → Embed in Qdrant → Populate Baserow")
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
        print(f"   Email: {final_state.get('header_metadata', {}).get('client_email', 'N/A')}")
        print(f"   Date: {final_state.get('header_metadata', {}).get('meeting_date', 'N/A')}")

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
            print(f"   ✅ Baserow: Check tables below")

        print("\n" + "=" * 80)
        print("🔍 VERIFICATION LINKS")
        print("=" * 80)
        print(f"\n📊 BASEROW TABLES:")
        print(f"   Clients:        http://localhost:8080/database/174/table/704/")
        print(f"   Meetings:       http://localhost:8080/database/174/table/705/")
        print(f"   Deals:          http://localhost:8080/database/174/table/706/")
        print(f"   Communications: http://localhost:8080/database/174/table/707/")
        print(f"   Sales Coaching: http://localhost:8080/database/174/table/708/")
        print(f"   Chunks:         http://localhost:8080/database/174/table/709/")

        print(f"\n🔗 QDRANT:")
        print(f"   Dashboard: http://localhost:6333/dashboard")
        print(f"   Collection: transcripts")
        print(f"   Filter by: transcript_id={transcript_id}")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
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
