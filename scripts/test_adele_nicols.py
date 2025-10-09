#!/usr/bin/env python3
"""
Test script to process Adele Nicols transcript through the complete pipeline to Baserow.
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
    print(f"🚀 STARTING PIPELINE TEST - ADELE NICOLS")
    print(f"{'='*80}\n")

    # Create the workflow
    app = create_master_workflow()

    # Run the pipeline
    print(f"📄 Processing transcript: {file_path.name}")
    print(f"📊 File size: {file_path.stat().st_size / 1024:.1f} KB\n")

    try:
        final_state = await app.ainvoke({"file_path": file_path})

        print(f"\n{'='*80}")
        print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
        print(f"{'='*80}\n")

        # Display results
        print("📋 RESULTS SUMMARY:")
        print(f"   Transcript ID: {final_state.get('transcript_id', 'N/A')}")

        # CRM Data
        if final_state.get('crm_data'):
            crm = final_state['crm_data']
            print(f"\n   👤 Client: {crm.get('client_name', 'N/A')}")
            print(f"   📞 Contact: {crm.get('client_email', 'N/A')}, {crm.get('client_phone', 'N/A')}")
            print(f"   💰 Deal Value: ${crm.get('deal', 0):,.2f}")
            print(f"   🎯 Next Steps: {crm.get('action_items', 'N/A')}")

        # Knowledge Graph
        if final_state.get('knowledge_graph_results'):
            kg = final_state['knowledge_graph_results']
            print(f"\n   🧠 Knowledge Graph: {kg.get('nodes_created', 0)} nodes, {kg.get('relationships_created', 0)} relationships")

        # Embeddings
        if final_state.get('embedding_results'):
            emb = final_state['embedding_results']
            print(f"   🔍 Vector Search: {emb.get('vectors_stored', 0)} embeddings stored")

        # Baserow persistence
        if final_state.get('baserow_results'):
            br = final_state['baserow_results']
            print(f"\n   💾 BASEROW PERSISTENCE:")
            print(f"      Client ID: {br.get('client_id', 'N/A')}")
            print(f"      Meeting ID: {br.get('meeting_id', 'N/A')}")
            print(f"      Deal ID: {br.get('deal_id', 'N/A')}")
            print(f"      Communication ID: {br.get('communication_id', 'N/A')}")
            print(f"      Coaching ID: {br.get('coaching_id', 'N/A')}")

        return final_state

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    # Path to Adele Nicols transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Adele Nicols: Estate Planning Advisor Meeting.txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        sys.exit(1)

    # Run the pipeline
    result = await run_pipeline(transcript_path)

    if result:
        print(f"\n{'='*80}")
        print("🎉 TEST COMPLETED SUCCESSFULLY - Check Baserow for data!")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
