#!/usr/bin/env python3
"""
Test script to process George Padron transcript through the complete pipeline.
This tests Pattern A header format (no blank lines) with human-in-the-loop evaluation.
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
    print(f"🚀 GEORGE PADRON PIPELINE TEST - PATTERN A HEADER")
    print(f"{'='*80}\n")

    # Create the workflow
    app = create_master_workflow()

    # Run the pipeline
    print(f"📄 Processing transcript: {file_path.name}")
    print(f"📊 File size: {file_path.stat().st_size / 1024:.1f} KB")
    print(f"🎯 Testing: Pattern A header + Full CRM integration\n")

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

        # Display comprehensive CRM data
        print(f"\n{'='*80}")
        print(f"📊 CRM DATA SUMMARY (Ready for Baserow Evaluation)")
        print(f"{'='*80}\n")

        if final_state.get('crm_data'):
            crm = final_state['crm_data']

            print("🆔 MEETING IDENTIFICATION:")
            print(f"   Meeting Title: {crm.get('meeting_title', 'N/A')}")
            print(f"   Transcript ID: {crm.get('transcript_id', 'N/A')}")
            print(f"   Meeting Date: {crm.get('meeting_date', 'N/A')}")
            print(f"   Filename: {crm.get('transcript_filename', 'N/A')}")

            print("\n👤 CLIENT PROFILE:")
            print(f"   Name: {crm.get('client_name', 'N/A')}")
            print(f"   Email: {crm.get('client_email', 'N/A')}")
            print(f"   Marital Status: {crm.get('marital_status', 'N/A')}")
            print(f"   Children: {crm.get('children_count', 0)}")
            print(f"   Estate Value: ${crm.get('estate_value', 0):,.2f}")
            print(f"   Real Estate Count: {crm.get('real_estate_count', 0)}")
            print(f"   LLC Interest: {crm.get('llc_interest', 'N/A')}")

            print("\n💰 DEAL INFORMATION:")
            print(f"   Product Discussed: {crm.get('product_discussed', 'N/A')}")
            print(f"   Deal Amount: ${crm.get('deal', 0):,.2f}")
            print(f"   Deposit: ${crm.get('deposit', 0):,.2f}")
            print(f"   Outcome: {crm.get('outcome', 'N/A')}")

            print("\n📝 SALES INSIGHTS:")
            print(f"   Objections Raised: {crm.get('objections_raised', 'N/A')}")
            print(f"   Next Steps: {crm.get('action_items', 'N/A')[:100]}...")

            print("\n📧 FOLLOW-UP CONTENT:")
            email_draft = crm.get('follow_up_email_draft', crm.get('email_draft', ''))
            if email_draft:
                lines = email_draft.split('\n')[:5]
                print(f"   Email Draft (first 5 lines):")
                for line in lines:
                    print(f"      {line[:80]}")

            print("\n📱 SOCIAL MEDIA:")
            social_quote = crm.get('social_media_quote', '')
            if social_quote:
                print(f"   Quote: {social_quote[:150]}...")

            print("\n👨‍🏫 COACHING INSIGHTS:")
            coaching = crm.get('coaching_insights', {})
            if isinstance(coaching, dict):
                strengths = coaching.get('strengths', [])
                opportunities = coaching.get('opportunities', [])
                print(f"   Strengths: {len(strengths)} identified")
                print(f"   Opportunities: {len(opportunities)} identified")
                if strengths:
                    print(f"   Top Strength: {strengths[0][:100]}...")
                if opportunities:
                    print(f"   Top Opportunity: {opportunities[0][:100]}...")

            print("\n📊 TRANSCRIPT SUMMARY:")
            summary = crm.get('transcript_summary', '')
            if summary:
                print(f"   {summary[:200]}...")

        # Knowledge Graph
        if final_state.get('knowledge_graph_results'):
            kg = final_state['knowledge_graph_results']
            print(f"\n🧠 KNOWLEDGE GRAPH:")
            print(f"   Nodes: {kg.get('nodes_created', 0)}")
            print(f"   Relationships: {kg.get('relationships_created', 0)}")

        # Embeddings
        if final_state.get('embedding_results'):
            emb = final_state['embedding_results']
            print(f"\n🔍 VECTOR SEARCH:")
            print(f"   Embeddings Stored: {emb.get('vectors_stored', 0)}")

        # Database persistence
        if final_state.get('db_save_status'):
            db = final_state['db_save_status']
            print(f"\n💾 DATABASE PERSISTENCE:")
            print(f"   PostgreSQL: {db.get('postgres_status', 'N/A')}")
            print(f"   Baserow: {db.get('baserow_status', 'N/A')}")

        # Generate Baserow access instructions
        print(f"\n{'='*80}")
        print(f"🔍 BASEROW EVALUATION INSTRUCTIONS")
        print(f"{'='*80}\n")

        print("1. Open Baserow at: http://localhost:8080")
        print("2. Navigate to the Clients table (Table 704)")
        print(f"3. Search for: George Padron")
        print(f"4. External ID: {final_state.get('crm_data', {}).get('transcript_id', 'N/A')}")
        print("\n📋 Fields to evaluate:")
        print("   ✓ client_name = 'George Padron'")
        print("   ✓ email = 'george.padron7@gmail.com'")
        print("   ✓ marital_status (check if populated)")
        print("   ✓ children_count (check value)")
        print("   ✓ estate_value (check amount)")
        print("   ✓ crm_json (contains meeting_title field)")
        print("\n5. Check related tables:")
        print("   - Meetings table (Table 705): Verify meeting record exists")
        print("   - Deals table (Table 706): Verify deal information")
        print("   - Communications table (Table 707): Verify email draft")
        print("   - Sales Coaching table (Table 708): Verify coaching feedback")

        return final_state

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    # Path to George Padron transcript
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/GEORGE PADRON: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        sys.exit(1)

    # Run the pipeline
    result = await run_pipeline(transcript_path)

    if result:
        print(f"\n{'='*80}")
        print("🎉 PIPELINE TEST COMPLETED - Ready for Human Evaluation!")
        print(f"{'='*80}\n")
        print("👉 Next step: Review the data in Baserow and verify accuracy")
        print("   Compare CRM fields above with actual transcript content")
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
