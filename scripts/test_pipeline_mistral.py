"""
Test full pipeline with Mistral 7B (faster for testing/development)
Expected completion time: 2-3 minutes (vs 10+ minutes with DeepSeek 33B)
"""
from config.settings import settings
from orchestrator.graph import app
import asyncio
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_pipeline_mistral():
    """Run full pipeline with Mistral 7B model"""
    print("=" * 80)
    print("FULL PIPELINE TEST - Mistral 7B")
    print("=" * 80)

    print(f"\n⚙️  Configuration:")
    print(f"   LLM Model: {settings.LLM_MODEL_NAME}")
    print(f"   Expected Speed: ⚡ Fast (2-3 minutes total)")

    # Use the test transcript from data/transcripts
    test_file = settings.WATCHER_DIRECTORY / "test_sprint01.txt"

    if not test_file.exists():
        print(f"\n❌ Test file not found: {test_file}")
        print(f"   Using real transcript instead...")
        test_file = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/John and Janice Suss: Estate Planning Advisor Meeting .txt")

    print(f"\n📄 Transcript: {test_file.name}")
    print(f"   Size: {test_file.stat().st_size / 1024:.1f} KB")

    print("\n🚀 Starting pipeline...")
    print("   Agents will run in this order:")
    print("   1. Parser → 2. Structuring → 3. Chunker")
    print("   4. [Parallel] Knowledge Analyst + Embedder")
    print("   5. [Parallel] Email + Social + Sales Coach")
    print("   6. CRM (aggregation)")
    print("   7. Persistence (PostgreSQL + Baserow sync)")
    print()

    start_time = time.time()

    try:
        result = await app.ainvoke({"file_path": test_file})
        elapsed = time.time() - start_time

        print("\n" + "=" * 80)
        print(f"✅ PIPELINE COMPLETE - {elapsed/60:.1f} minutes")
        print("=" * 80)

        # Results summary
        transcript_id = result.get("transcript_id", "N/A")
        print(f"\n📊 Results:")
        print(f"   Transcript ID: {transcript_id}")
        print(f"   Chunks: {len(result.get('chunks', []))}")
        print(
            f"   Dialogue turns: {len(result.get('structured_dialogue', []))}")

        # Check persistence
        db_status = result.get("db_save_status", {})
        if db_status.get("persistence_status") == "success":
            print(f"\n✅ Data saved successfully:")
            print(f"   PostgreSQL: ✅")
            print(f"   Baserow: ✅ (all 5 tables)")
            print(f"   External ID: {transcript_id}")

        # Check extracted data
        crm_data = result.get("crm_data", {})
        if crm_data:
            print(f"\n📋 CRM Data extracted:")
            if "client_name" in crm_data:
                print(f"   Client: {crm_data.get('client_name', 'N/A')}")
            if "deal" in crm_data:
                print(f"   Deal: ${crm_data.get('deal', 0):,.2f}")
            if "outcome" in crm_data:
                print(f"   Outcome: {crm_data.get('outcome', 'N/A')}")

        print(f"\n🎯 Performance:")
        print(
            f"   Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"   Model: {settings.LLM_MODEL_NAME}")

        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)
        print(f"\n🔍 Check your data:")
        print(f"   1. Baserow UI: http://localhost:8080")
        print(f"      Search for: external_id = {transcript_id}")
        print(f"   2. Qdrant: http://localhost:6333/dashboard")
        print(f"      Collection: transcripts")
        print(f"   3. Neo4j: http://localhost:7474")
        print(
            f"      Query: MATCH (n) WHERE n.transcript_id = '{transcript_id}' RETURN n")

        print("\n✅ Success! Pipeline completed with Mistral 7B")
        print("   Much faster than DeepSeek 33B for development/testing!")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Pipeline failed after {elapsed:.1f} seconds")
        print(f"   Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_pipeline_mistral())
