"""
Test Baserow integration by uploading a sample transcript
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import app
from config.settings import settings


async def test_baserow_integration():
    """Test full pipeline with Baserow sync"""
    print("=" * 70)
    print("Testing Baserow Integration")
    print("=" * 70)

    # Find a test transcript
    transcript_dir = settings.WATCHER_DIRECTORY
    transcripts = list(transcript_dir.glob("*.txt"))

    if not transcripts:
        print("❌ No transcripts found in", transcript_dir)
        print("Please add a test transcript to test Baserow integration.")
        return

    test_file = transcripts[0]
    print(f"\n📄 Testing with transcript: {test_file.name}")

    # Run the ingestion pipeline
    print("\n🚀 Running ingestion pipeline...")
    try:
        result = await app.ainvoke({"file_path": test_file})

        print("\n" + "=" * 70)
        print("PIPELINE RESULT")
        print("=" * 70)

        if result.get("db_save_status", {}).get("persistence_status") == "success":
            print("✅ Pipeline completed successfully!")
            print(f"   - PostgreSQL: Saved")
            print(f"   - Baserow: Check http://localhost:8080 for synced data")
            print(f"   - Transcript ID: {result.get('transcript_id', 'N/A')}")
        else:
            print("⚠️ Pipeline completed with warnings")
            print(f"Result: {result}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Next: Check Baserow UI at http://localhost:8080")
    print("Look for data in all 5 tables linked by external_id")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_baserow_integration())
