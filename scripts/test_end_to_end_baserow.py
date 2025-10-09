#!/usr/bin/env python3
"""
End-to-end test: Process AJ Caruso transcript through complete pipeline to Baserow.
Tests: Parser → Structuring → Chunker → Embedder → KnowledgeAnalyst → CRM → Baserow
"""
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.pipeline import run_pipeline


async def test_end_to_end():
    """Run complete pipeline on AJ Caruso transcript and verify Baserow output"""
    print("=" * 80)
    print("END-TO-END PIPELINE TEST: AJ Caruso → Baserow")
    print("=" * 80)

    # AJ Caruso transcript from McAdams Transcripts folder
    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/AJ Caruso: Estate Planning Advisor Meeting .txt")

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        return 1

    print(f"\n📄 Transcript: {transcript_path.name}")
    print(f"📊 Size: {transcript_path.stat().st_size / 1024:.1f} KB")

    print("\n🚀 Running COMPLETE PIPELINE...")
    print("   Pipeline: Parser → Structuring → Chunker → Embedder → KnowledgeAnalyst → CRM → Baserow")
    print("-" * 80)

    try:
        # Run complete pipeline
        final_state = await run_pipeline(file_path=transcript_path)

        print("\n" + "=" * 80)
        print("PIPELINE RESULTS")
        print("=" * 80)

        # Extract key results
        transcript_id = final_state.get('transcript_id')
        extracted_entities = final_state.get('extracted_entities', {})
        crm_data = final_state.get('crm_data', {})
        db_save_status = final_state.get('db_save_status')

        print(f"\n✅ Transcript ID: {transcript_id}")

        print(f"\n📊 EXTRACTED ENTITIES (via Hybrid Search):")
        print(json.dumps(extracted_entities, indent=2))

        print(f"\n💼 CRM DATA:")
        print(json.dumps(crm_data, indent=2))

        print(f"\n💾 DATABASE SAVE STATUS:")
        print(f"   {db_save_status}")

        # Verify Baserow save
        if db_save_status and "success" in str(db_save_status).lower():
            print("\n🎉 SUCCESS: Transcript processed and saved to Baserow!")

            # Verify in Baserow
            print("\n🔍 Verifying Baserow record...")
            import requests

            # Check Clients table for this transcript
            response = requests.get(
                f"http://localhost:8080/api/database/rows/table/704/?user_field_names=true&filter__external_id__equal={transcript_id}",
                headers={"Authorization": "Token 6TElBEHaafiG4nmajttcnaN7TZEIioi7"}
            )

            if response.ok:
                data = response.json()
                if data['count'] > 0:
                    client = data['results'][0]
                    print(f"\n✅ BASEROW VERIFICATION:")
                    print(f"   Client Name: {client.get('client_name')}")
                    print(f"   Email: {client.get('email')}")
                    print(f"   External ID: {client.get('external_id')}")
                    print(f"   Marital Status: {client.get('marital_status', {}).get('value') if isinstance(client.get('marital_status'), dict) else client.get('marital_status')}")
                    print(f"   Children: {client.get('children_count')}")
                    print(f"   State: {client.get('state_of_residence', {}).get('value') if isinstance(client.get('state_of_residence'), dict) else client.get('state_of_residence')}")

                    return 0
                else:
                    print(f"⚠️  Record not found in Baserow for transcript_id: {transcript_id}")
                    return 1
            else:
                print(f"❌ Failed to verify Baserow: {response.status_code}")
                return 1
        else:
            print(f"\n❌ FAILED: Database save unsuccessful")
            print(f"   Status: {db_save_status}")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_end_to_end())
    sys.exit(exit_code)
