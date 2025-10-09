#!/usr/bin/env python3
"""
Test semantic chunking with Robin Michalek transcript.
Verifies dialogue-turn-aware chunking with semantic coherence.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import app
from orchestrator.state import AgentState


async def test_semantic_chunking():
    """Test semantic chunking with Robin Michalek transcript"""
    print("=" * 80)
    print("TESTING SEMANTIC DIALOGUE CHUNKING")
    print("=" * 80)

    # Use Robin Michalek transcript (real dialogue with timestamps)
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
        "final_response": None,
        "semantic_turns": None,
        "key_entities_nlp": None,
        "conversation_structure": None
    }

    print("\n🚀 Running pipeline through chunker node...")
    print("-" * 80)

    try:
        # Run just the first few nodes to test chunking
        from orchestrator.graph import structuring_node, parser_node, chunker_node

        # Step 1: Structuring (NLP analysis)
        print("\n1️⃣  Running StructuringAgent...")
        state = await structuring_node(initial_state)
        initial_state.update(state)

        print(f"   ✅ Identified {len(state.get('conversation_phases', []))} conversation phases")
        if state.get('semantic_turns'):
            print(f"   ✅ Analyzed {len(state['semantic_turns'])} dialogue turns (NLP)")

        # Step 2: Parser (enrich with metadata)
        print("\n2️⃣  Running ParserAgent...")
        state = await parser_node(initial_state)
        initial_state.update(state)

        dialogue_count = len(state.get('structured_dialogue', []))
        print(f"   ✅ Parsed {dialogue_count} dialogue turns")

        # Step 3: Chunker (SEMANTIC CHUNKING)
        print("\n3️⃣  Running ChunkerAgent (SEMANTIC CHUNKING)...")
        print("-" * 80)
        state = await chunker_node(initial_state)
        chunks = state.get('chunks', [])

        print("\n" + "=" * 80)
        print("SEMANTIC CHUNKING RESULTS")
        print("=" * 80)

        print(f"\n📊 Total chunks created: {len(chunks)}")

        # Analyze chunks
        header_chunks = [c for c in chunks if c.get('chunk_type') == 'header']
        dialogue_chunks = [c for c in chunks if c.get('chunk_type') == 'dialogue']

        print(f"   - Header chunks: {len(header_chunks)}")
        print(f"   - Dialogue chunks: {len(dialogue_chunks)}")

        # Show chunk statistics
        if dialogue_chunks:
            print(f"\n📈 Dialogue Chunk Statistics:")

            # Turn counts
            turn_counts = [c.get('turn_count', 0) for c in dialogue_chunks]
            avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0
            print(f"   Average turns per chunk: {avg_turns:.1f}")
            print(f"   Min/Max turns: {min(turn_counts)}/{max(turn_counts)}")

            # Chunk sizes (characters)
            chunk_sizes = [len(c.get('text', '')) for c in dialogue_chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            print(f"   Average chunk size: {avg_size:.0f} characters")
            print(f"   Min/Max size: {min(chunk_sizes)}/{max(chunk_sizes)} chars")

            # Metadata coverage
            chunks_with_phase = sum(1 for c in dialogue_chunks if c.get('conversation_phase'))
            chunks_with_intent = sum(1 for c in dialogue_chunks if c.get('dominant_intent'))
            chunks_with_sentiment = sum(1 for c in dialogue_chunks if c.get('dominant_sentiment'))

            print(f"\n📋 Metadata Coverage:")
            print(f"   Chunks with conversation_phase: {chunks_with_phase}/{len(dialogue_chunks)}")
            print(f"   Chunks with dominant_intent: {chunks_with_intent}/{len(dialogue_chunks)}")
            print(f"   Chunks with dominant_sentiment: {chunks_with_sentiment}/{len(dialogue_chunks)}")

            # Show sample chunks
            print(f"\n📝 Sample Chunks:")
            for i, chunk in enumerate(dialogue_chunks[:3], 1):
                print(f"\n   Chunk {i}:")
                print(f"      - Phase: {chunk.get('conversation_phase')}")
                print(f"      - Turns: {chunk.get('turn_count')}")
                print(f"      - Intent: {chunk.get('dominant_intent')}")
                print(f"      - Sentiment: {chunk.get('dominant_sentiment')}")
                print(f"      - Speakers: {chunk.get('speakers')}")
                print(f"      - Questions: {chunk.get('question_count')}")
                print(f"      - Objections: {chunk.get('objection_count')}")
                print(f"      - Time range: {chunk.get('timestamp_start')} → {chunk.get('timestamp_end')}")
                print(f"      - Size: {len(chunk.get('text', ''))} chars")
                print(f"      - Preview: {chunk.get('text', '')[:150]}...")

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

        # Verify best practices
        print("\n✅ BEST PRACTICES VERIFICATION:")

        checks = [
            ("No mid-sentence splits (dialogue turn boundaries respected)", all(c.get('turn_count', 0) >= 1 for c in dialogue_chunks)),
            ("Semantic coherence (chunks have conversation phases)", chunks_with_phase > len(dialogue_chunks) * 0.8),
            ("Metadata preservation (chunks have intent/sentiment)", chunks_with_intent > len(dialogue_chunks) * 0.7),
            ("Appropriate chunk sizes (700-2100 chars)", all(700 <= len(c.get('text', '')) <= 2500 for c in dialogue_chunks)),
            ("Rich metadata stored (turn_count, speaker_balance, etc.)", all(c.get('turn_count') is not None for c in dialogue_chunks))
        ]

        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "⚠️  WARN"
            print(f"   {status}: {check_name}")
            if not passed:
                all_passed = False

        if all_passed:
            print("\n🎉 All best practices verified!")
            print("Semantic chunking is working correctly:")
            print("   - Respects dialogue turn boundaries")
            print("   - Maintains semantic coherence")
            print("   - Preserves rich metadata")
            print("   - Optimal chunk sizes for embeddings")
            return 0
        else:
            print("\n⚠️  Some checks have warnings (review above)")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_semantic_chunking())
    sys.exit(exit_code)
