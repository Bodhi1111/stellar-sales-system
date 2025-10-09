#!/usr/bin/env python3
"""
Comprehensive test of the redesigned Intelligence First architecture.
Tests the new sequence: Structuring → Parser → Chunker → Embedder → Knowledge Analyst
"""
import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import app
from orchestrator.state import AgentState


async def test_redesigned_architecture():
    """Test the complete redesigned pipeline with Sylvia Flynn transcript"""
    print("=" * 80)
    print("TESTING REDESIGNED ARCHITECTURE")
    print("New Sequence: Structuring → Parser → Chunker → Embedder → Knowledge Analyst")
    print("=" * 80)
    
    # Use Robin Michalek transcript (68 KB)
    transcript_path = project_root / "data" / "transcripts" / "Robin Michalek: Estate Planning Advisor Meeting .txt"
    
    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found at {transcript_path}")
        return
    
    print(f"\n📄 Testing with: {transcript_path.name}")
    print(f"📊 File size: {transcript_path.stat().st_size / 1024:.1f} KB")
    
    # Initialize state
    initial_state: AgentState = {
        "file_path": transcript_path,
        "transcript_id": None,
        "chunks": None,
        "raw_text": None,
        "structured_dialogue": None,
        "conversation_phases": None,
        "extracted_data": None,
        "extracted_entities": None,
        "crm_data": None,
        "email_draft": None,
        "social_content": None,
        "coaching_feedback": None,
        "db_save_status": None,
        "historian_status": None,
        "original_request": None,
        "plan": None,
        "intermediate_steps": None,
        "verification_history": None,
        "clarification_question": None,
        "final_response": None
    }
    
    print("\n🚀 Starting pipeline execution...")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        # Run the complete workflow
        final_state = await app.ainvoke(initial_state)
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("PIPELINE EXECUTION COMPLETE")
        print("=" * 80)
        print(f"\n⏱️  Total execution time: {elapsed_time / 60:.2f} minutes ({elapsed_time:.1f} seconds)")
        
        # Verify architecture changes
        print("\n" + "=" * 80)
        print("ARCHITECTURE VERIFICATION")
        print("=" * 80)
        
        # 1. Check conversation phases (from Structuring)
        phases = final_state.get("conversation_phases", [])
        print(f"\n1️⃣  StructuringAgent (runs FIRST):")
        print(f"   ✓ Identified {len(phases)} conversation phases")
        if len(phases) >= 8:
            print(f"   ✅ PASS: Found {len(phases)} phases (expected 8-15)")
        else:
            print(f"   ⚠️  WARNING: Only {len(phases)} phases (expected 8-15)")
        
        if phases:
            print(f"   Sample phases:")
            for phase in phases[:5]:
                print(f"      - {phase.get('start_timestamp')}: {phase.get('phase')}")
        
        # 2. Check structured dialogue (from Parser)
        dialogue = final_state.get("structured_dialogue", [])
        print(f"\n2️⃣  ParserAgent (enriches with phases):")
        print(f"   ✓ Parsed {len(dialogue)} dialogue turns")
        
        # Check if dialogue turns have conversation_phase metadata
        turns_with_phase = sum(1 for turn in dialogue if turn.get("conversation_phase"))
        if turns_with_phase > 0:
            print(f"   ✅ PASS: {turns_with_phase}/{len(dialogue)} turns enriched with conversation_phase")
            print(f"   Sample enriched turns:")
            for turn in dialogue[:3]:
                phase = turn.get("conversation_phase", "N/A")
                print(f"      - [{turn['timestamp']}] {turn['speaker']}: phase='{phase}'")
        else:
            print(f"   ⚠️  WARNING: No turns have conversation_phase metadata")
        
        # 3. Check chunks (from Chunker)
        chunks = final_state.get("chunks", [])
        print(f"\n3️⃣  ChunkerAgent (creates metadata-rich chunks):")
        print(f"   ✓ Created {len(chunks)} chunks")
        
        # Check if chunks are dictionaries with metadata
        if chunks and isinstance(chunks[0], dict):
            chunks_with_phase = sum(1 for c in chunks if c.get("conversation_phase"))
            print(f"   ✅ PASS: Chunks are dictionaries (not plain text)")
            print(f"   ✅ PASS: {chunks_with_phase}/{len(chunks)} chunks have conversation_phase metadata")
            
            # Show sample chunk metadata
            print(f"   Sample chunk metadata:")
            for i, chunk in enumerate(chunks[:3]):
                if isinstance(chunk, dict):
                    print(f"      Chunk {i}:")
                    print(f"         - type: {chunk.get('chunk_type')}")
                    print(f"         - phase: {chunk.get('conversation_phase')}")
                    print(f"         - speakers: {chunk.get('speakers')}")
                    print(f"         - time range: {chunk.get('timestamp_start')} → {chunk.get('timestamp_end')}")
        else:
            print(f"   ⚠️  WARNING: Chunks are plain text (expected dictionaries)")
        
        # 4. Check extracted entities (from Knowledge Analyst)
        entities = final_state.get("extracted_entities", {})
        print(f"\n4️⃣  KnowledgeAnalystAgent (RAG-based extraction):")
        if entities:
            print(f"   ✅ PASS: Successfully extracted entities")
            print(f"   Extracted data:")
            print(f"      - Client: {entities.get('client_name', 'N/A')}")
            print(f"      - Email: {entities.get('client_email', 'N/A')}")
            print(f"      - Meeting Date: {entities.get('meeting_date', 'N/A')}")
            print(f"      - Duration: {entities.get('duration_minutes', 'N/A')} minutes")
            
            # Check if duration_minutes was captured (header format fix)
            if entities.get('duration_minutes'):
                print(f"   ✅ PASS: Header duration_minutes captured correctly")
            else:
                print(f"   ⚠️  WARNING: duration_minutes missing from header")
        else:
            print(f"   ⚠️  WARNING: No entities extracted")
        
        # 5. Check transcript_id
        transcript_id = final_state.get("transcript_id")
        print(f"\n5️⃣  Transcript ID:")
        print(f"   ✓ ID: {transcript_id}")
        
        # 6. Performance comparison
        print(f"\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS")
        print("=" * 80)
        print(f"\n⏱️  Previous architecture: ~12 minutes")
        print(f"⏱️  New architecture: {elapsed_time / 60:.2f} minutes")
        
        if elapsed_time < 720:  # Less than 12 minutes
            improvement = ((720 - elapsed_time) / 720) * 100
            print(f"✅ IMPROVEMENT: {improvement:.1f}% faster")
        else:
            print(f"⚠️  No improvement detected")
        
        # 7. Final status
        print(f"\n" + "=" * 80)
        print("FINAL STATUS")
        print("=" * 80)
        
        db_status = final_state.get("db_save_status", {})
        print(f"\n💾 Database persistence: {db_status.get('status', 'unknown')}")
        
        if final_state.get("email_draft"):
            print(f"✅ Email draft generated")
        if final_state.get("social_content"):
            print(f"✅ Social content generated")
        if final_state.get("coaching_feedback"):
            print(f"✅ Coaching feedback generated")
        if final_state.get("crm_data"):
            print(f"✅ CRM data aggregated")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ ERROR: Pipeline failed after {elapsed_time:.1f} seconds")
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_redesigned_architecture())
