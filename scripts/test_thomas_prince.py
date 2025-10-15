#!/usr/bin/env python3
"""Test ingestion pipeline with Thomas Prince transcript"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.graph import create_master_workflow
from orchestrator.state import AgentState
from config.settings import settings


async def main():
    """Run ingestion pipeline on Thomas Prince transcript"""

    transcript_path = Path("/Users/joshuavaughan/Library/CloudStorage/GoogleDrive-jvaughan27@gmail.com/.shortcut-targets-by-id/1oyouGXIJLyId2y2H-JJVYay9GFpnLTDK/McAdams Transcripts/Thomas Prince: Estate Planning Advisor Meeting.txt")

    print(f"\n{'='*80}")
    print(f"🚀 Processing: {transcript_path.name}")
    print(f"{'='*80}\n")

    if not transcript_path.exists():
        print(f"❌ Error: Transcript not found at {transcript_path}")
        return

    # Initialize state
    initial_state = AgentState(
        file_path=str(transcript_path),
        raw_transcript="",
        parsed_data={},
        structured_data={},
        chunks=[],
        chunk_metadata=[],
        knowledge_graph={},
        embeddings=[],
        email_draft="",
        social_posts=[],
        coaching_feedback="",
        crm_summary={},
        persistence_result={},
        errors=[]
    )

    # Create and run workflow
    app = create_master_workflow()

    print("📊 Starting ingestion pipeline...\n")

    final_state = await app.ainvoke(initial_state)

    print(f"\n{'='*80}")
    print("✅ PIPELINE COMPLETE")
    print(f"{'='*80}\n")

    # Display results
    if final_state.get("errors"):
        print("⚠️  ERRORS:")
        for error in final_state["errors"]:
            print(f"  - {error}")
        print()

    if final_state.get("parsed_data"):
        print("📄 Parsed Data:")
        parsed = final_state["parsed_data"]
        print(f"  - Meeting Title: {parsed.get('meeting_title', 'N/A')}")
        print(f"  - Participants: {len(parsed.get('participants', []))} detected")
        print(f"  - Duration: {parsed.get('duration', 'N/A')}")
        print()

    if final_state.get("chunks"):
        print(f"📦 Chunks: {len(final_state['chunks'])} created")
        print()

    if final_state.get("knowledge_graph"):
        kg = final_state["knowledge_graph"]
        print("🧠 Knowledge Graph:")
        print(f"  - Entities: {len(kg.get('entities', []))}")
        print(f"  - Relationships: {len(kg.get('relationships', []))}")
        print()

    if final_state.get("embeddings"):
        print(f"🔢 Embeddings: {len(final_state['embeddings'])} vectors generated")
        print()

    if final_state.get("crm_summary"):
        crm = final_state["crm_summary"]
        print("📊 CRM Summary:")
        print(f"  - Lead Score: {crm.get('lead_score', 'N/A')}")
        print(f"  - Next Actions: {len(crm.get('next_actions', []))}")
        print()

    if final_state.get("persistence_result"):
        pers = final_state["persistence_result"]
        print("💾 Persistence:")
        print(f"  - Status: {pers.get('status', 'N/A')}")
        print(f"  - Record ID: {pers.get('transcript_id', 'N/A')}")
        print()

    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
