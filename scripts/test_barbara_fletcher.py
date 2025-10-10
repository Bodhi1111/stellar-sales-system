#!/usr/bin/env python3
"""
Test script to process Barbara Fletcher transcript through the complete pipeline.
This tests the header extraction enhancement with a fresh, untouched transcript.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import create_master_workflow


async def run_pipeline(file_path: Path):
    """Run the complete ingestion pipeline including Baserow persistence."""
    print(f"\n{'='*80}")
    print(f"🚀 HEADER EXTRACTION ENHANCEMENT TEST - BARBARA FLETCHER")
    print(f"{'='*80}\n")

    # Create the workflow
    app = create_master_workflow()

    # Run the pipeline
    print(f"📄 Processing transcript: {file_path.name}")
    print(f"📊 File size: {file_path.stat().st_size / 1024:.1f} KB")
    print(f"🎯 Testing: Header metadata extraction + CRM integration\n")

    try:
        final_state = await app.ainvoke({"file_path": file_path})

        print(f"\n{'='*80}")
        print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"{'='*80}\n")

        # Display header metadata extraction results
        print("📋 HEADER METADATA EXTRACTION:")
        if final_state.get('header_metadata'):
            hm = final_state['header_metadata']
            print(f"   ✅ meeting_title: {hm.get('meeting_title', 'N/A')}")
            print(f"   ✅ client_name: {hm.get('client_name', 'N/A')}")
            print(f"   ✅ client_email: {hm.get('client_email', 'N/A')}")
            print(f"   ✅ meeting_date: {hm.get('meeting_date', 'N/A')}")
            print(f"   ✅ meeting_time: {hm.get('meeting_time', 'N/A')}")
            print(f"   ✅ transcript_id: {hm.get('transcript_id', 'N/A')}")
            print(f"   ✅ meeting_url: {hm.get('meeting_url', 'N/A')}")
            print(f"   ✅ duration_minutes: {hm.get('duration_minutes', 'N/A')}")
        else:
            print("   ❌ No header metadata extracted!")

        # Display CRM data results
        print(f"\n📋 CRM DATA (using header metadata):")
        print(f"   Transcript ID: {final_state.get('transcript_id', 'N/A')}")

        if final_state.get('crm_data'):
            crm = final_state['crm_data']
            print(f"\n   🆔 Meeting Title: {crm.get('meeting_title', 'N/A')}")
            print(f"   👤 Client: {crm.get('client_name', 'N/A')}")
            print(f"   📞 Contact: {crm.get('client_email', 'N/A')}")
            print(f"   📅 Meeting Date: {crm.get('meeting_date', 'N/A')}")
            print(f"   💰 Deal Value: ${crm.get('deal', 0):,.2f}")
            print(f"   🎯 Next Steps: {crm.get('action_items', 'N/A')[:100]}...")

        # Knowledge Graph
        if final_state.get('knowledge_graph_results'):
            kg = final_state['knowledge_graph_results']
            print(f"\n   🧠 Knowledge Graph: {kg.get('nodes_created', 0)} nodes, {kg.get('relationships_created', 0)} relationships")

        # Embeddings
        if final_state.get('embedding_results'):
            emb = final_state['embedding_results']
            print(f"   🔍 Vector Search: {emb.get('vectors_stored', 0)} embeddings stored")

        # Database persistence
        if final_state.get('db_save_status'):
            db = final_state['db_save_status']
            print(f"\n   💾 DATABASE PERSISTENCE:")
            print(f"      PostgreSQL: {db.get('postgres_status', 'N/A')}")
            print(f"      Baserow: {db.get('baserow_status', 'N/A')}")

        # Verification checks
        print(f"\n{'='*80}")
        print("🔍 VERIFICATION CHECKS:")
        print(f"{'='*80}")

        checks_passed = 0
        checks_total = 5

        # Check 1: Header metadata extracted
        if final_state.get('header_metadata') and final_state['header_metadata'].get('meeting_title'):
            print("   ✅ Check 1: Header metadata extracted successfully")
            checks_passed += 1
        else:
            print("   ❌ Check 1: Header metadata extraction failed")

        # Check 2: Meeting title in CRM
        if final_state.get('crm_data') and final_state['crm_data'].get('meeting_title'):
            print("   ✅ Check 2: Meeting title populated in CRM")
            checks_passed += 1
        else:
            print("   ❌ Check 2: Meeting title missing from CRM")

        # Check 3: Client name matches header
        if (final_state.get('header_metadata') and final_state.get('crm_data') and
            final_state['header_metadata'].get('client_name') == final_state['crm_data'].get('client_name')):
            print("   ✅ Check 3: Client name matches between header and CRM")
            checks_passed += 1
        else:
            print("   ❌ Check 3: Client name mismatch between header and CRM")

        # Check 4: Email matches header
        if (final_state.get('header_metadata') and final_state.get('crm_data') and
            final_state['header_metadata'].get('client_email') == final_state['crm_data'].get('client_email')):
            print("   ✅ Check 4: Email matches between header and CRM")
            checks_passed += 1
        else:
            print("   ❌ Check 4: Email mismatch between header and CRM")

        # Check 5: Database persistence successful
        if final_state.get('db_save_status') and final_state['db_save_status'].get('baserow_status') == 'success':
            print("   ✅ Check 5: Database persistence successful")
            checks_passed += 1
        else:
            print("   ❌ Check 5: Database persistence failed")

        print(f"\n   📊 Verification Score: {checks_passed}/{checks_total} checks passed")

        return final_state, checks_passed == checks_total

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, False


async def main():
    # Path to Barbara Fletcher transcript (fresh, untested)
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Barbara Fletcher: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        sys.exit(1)

    # Run the pipeline
    result, all_checks_passed = await run_pipeline(transcript_path)

    if result and all_checks_passed:
        print(f"\n{'='*80}")
        print("🎉 TEST COMPLETED SUCCESSFULLY - ALL CHECKS PASSED!")
        print(f"{'='*80}\n")
    elif result:
        print(f"\n{'='*80}")
        print("⚠️ TEST COMPLETED WITH WARNINGS - Some checks failed")
        print(f"{'='*80}\n")
        sys.exit(1)
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
