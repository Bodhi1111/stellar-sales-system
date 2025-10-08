"""
Test the full ingestion pipeline with a real transcript
Runs end-to-end: Parser → Structuring → Chunking → Intelligence Core → CRM → Persistence → Baserow
"""
from orchestrator.graph import app
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_full_pipeline():
    """Run complete ingestion pipeline on real McAdams transcript"""
    print("=" * 80)
    print("FULL INGESTION PIPELINE TEST - Real Transcript")
    print("=" * 80)

    # Path to the real transcript
    transcript_path = Path(
        "/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/John and Janice Suss: Estate Planning Advisor Meeting .txt")

    # Verify file exists
    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript file not found at:")
        print(f"   {transcript_path}")
        print("\n💡 TIP: Make sure the file path is correct and accessible")
        return

    print(f"\n📄 Transcript File:")
    print(f"   Path: {transcript_path.name}")
    print(f"   Size: {transcript_path.stat().st_size / 1024:.1f} KB")
    print(f"   Exists: ✅")

    print("\n🚀 Starting ingestion pipeline...")
    print("   This will process through all agents:")
    print("   1. Parser (extract transcript_id and structure dialogue)")
    print("   2. Structuring (analyze conversation phases)")
    print("   3. Chunker (segment content)")
    print("   4. Knowledge Analyst (extract entities, build Neo4j graph)")
    print("   5. Embedder (create Qdrant vector embeddings)")
    print("   6. Email Agent (generate follow-up email)")
    print("   7. Social Agent (generate social content)")
    print("   8. Sales Coach Agent (provide coaching feedback)")
    print("   9. CRM Agent (aggregate all insights)")
    print("   10. Persistence Agent (save to PostgreSQL + sync to Baserow)")
    print()

    try:
        # Run the pipeline
        print("⏳ Processing (this may take 2-5 minutes due to LLM inference)...\n")
        result = await app.ainvoke({"file_path": transcript_path})

        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 80)

        # Display results
        transcript_id = result.get("transcript_id", "N/A")
        print(f"\n📊 Results Summary:")
        print(f"   Transcript ID: {transcript_id}")
        print(f"   Chunks created: {len(result.get('chunks', []))}")
        print(
            f"   Dialogue turns: {len(result.get('structured_dialogue', []))}")

        # Check extracted entities
        extracted_entities = result.get("extracted_entities", {})
        if extracted_entities:
            print(f"\n✅ Knowledge Analyst - Entities extracted:")
            print(f"   Fields extracted: {len(extracted_entities)}")
            if "customer_name" in extracted_entities:
                print(
                    f"   Customer: {extracted_entities.get('customer_name', 'N/A')}")

        # Check email draft
        email_draft = result.get("email_draft", "")
        if email_draft:
            print(f"\n✅ Email Agent - Draft generated:")
            print(f"   Length: {len(email_draft)} characters")

        # Check social content
        social_content = result.get("social_content", {})
        if social_content:
            print(f"\n✅ Social Agent - Content created:")
            print(f"   Fields: {list(social_content.keys())}")

        # Check coaching feedback
        coaching_feedback = result.get("coaching_feedback", {})
        if coaching_feedback:
            print(f"\n✅ Sales Coach Agent - Feedback provided:")
            print(f"   Fields: {list(coaching_feedback.keys())}")

        # Check CRM data
        crm_data = result.get("crm_data", {})
        if crm_data:
            print(f"\n✅ CRM Agent - Data aggregated:")
            print(f"   Fields: {len(crm_data)}")
            if "client_name" in crm_data:
                print(f"   Client: {crm_data.get('client_name', 'N/A')}")
            if "deal" in crm_data:
                print(f"   Deal Amount: ${crm_data.get('deal', 0):,.2f}")
            if "outcome" in crm_data:
                print(f"   Outcome: {crm_data.get('outcome', 'N/A')}")

        # Check persistence status
        db_save_status = result.get("db_save_status", {})
        persistence_status = db_save_status.get(
            "persistence_status", "unknown")

        print(f"\n✅ Persistence Agent:")
        if persistence_status == "success":
            print(f"   PostgreSQL: ✅ Saved successfully")
            print(f"   Baserow: ✅ Synced successfully")
            print(f"   External ID: {transcript_id}")
        else:
            print(f"   Status: ❌ {persistence_status}")
            if "message" in db_save_status:
                print(f"   Error: {db_save_status['message']}")

        # Provide next steps
        print("\n" + "=" * 80)
        print("VERIFICATION STEPS")
        print("=" * 80)
        print(f"\n1. PostgreSQL Database:")
        print(
            f"   Query: SELECT * FROM transcripts WHERE external_id = '{transcript_id}';")
        print(f"   Check: Verify record exists with all data fields populated")

        print(f"\n2. Baserow Database:")
        print(f"   URL: http://localhost:8080")
        print(
            f"   Check: Look for records in all 5 tables with external_id = {transcript_id}")
        print(f"   Tables: Clients, Meetings, Deals, Communications, Sales Coaching")

        print(f"\n3. Qdrant Vector Database:")
        print(f"   URL: http://localhost:6333/dashboard")
        print(f"   Collection: transcripts")
        print(
            f"   Check: Search for vectors with metadata.transcript_id = {transcript_id}")

        print(f"\n4. Neo4j Graph Database:")
        print(f"   URL: http://localhost:7474")
        print(
            f"   Query: MATCH (n) WHERE n.transcript_id = '{transcript_id}' RETURN n;")
        print(f"   Check: Verify entities and relationships were created")

        print("\n" + "=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ PIPELINE ERROR")
        print("=" * 80)
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

        print("\n💡 Common issues:")
        print("   - LLM (Ollama) not running: docker ps | grep ollama")
        print("   - Database not accessible: Check docker-compose services")
        print("   - Model not loaded: ollama pull deepseek-coder:33b-instruct")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
