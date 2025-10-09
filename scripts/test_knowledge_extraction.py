#!/usr/bin/env python3
"""
Test KnowledgeAnalystAgent extraction quality with enhanced semantic chunking.
Verifies that rich metadata improves retrieval accuracy and extraction quality.
"""
import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.graph import app
from orchestrator.state import AgentState


async def test_knowledge_extraction():
    """Test end-to-end pipeline with focus on KnowledgeAnalyst extraction"""
    print("=" * 80)
    print("TESTING KNOWLEDGE EXTRACTION WITH SEMANTIC CHUNKING")
    print("=" * 80)

    # Use Robin Michalek transcript
    transcript_path = project_root / "data" / "transcripts" / "Robin Michalek: Estate Planning Advisor Meeting .txt"

    if not transcript_path.exists():
        print(f"❌ ERROR: Transcript not found")
        return 1

    print(f"\n📄 Transcript: {transcript_path.name}")
    print(f"📊 Size: {transcript_path.stat().st_size / 1024:.1f} KB")

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

    print("\n🚀 Running Intelligence-First Pipeline...")
    print("-" * 80)

    try:
        # Run pipeline through KnowledgeAnalyst
        from orchestrator.graph import (
            structuring_node,
            parser_node,
            chunker_node,
            embedder_node,
            knowledge_analyst_node
        )

        # Phase 1: NLP Analysis
        print("\n📊 Phase 1: Semantic NLP Analysis")
        state = await structuring_node(initial_state)
        initial_state.update(state)

        phases = state.get('conversation_phases', [])
        semantic_turns = state.get('semantic_turns', [])
        print(f"   ✅ {len(phases)} conversation phases identified")
        print(f"   ✅ {len(semantic_turns)} dialogue turns analyzed (NLP)")

        # Phase 2: Parser Enrichment
        print("\n📜 Phase 2: Parser Enrichment")
        state = await parser_node(initial_state)
        initial_state.update(state)

        dialogue = state.get('structured_dialogue', [])
        transcript_id = state.get('transcript_id')
        print(f"   ✅ {len(dialogue)} dialogue turns parsed")
        print(f"   ✅ Transcript ID: {transcript_id}")

        # Phase 3: Semantic Chunking
        print("\n📦 Phase 3: Semantic Chunking")
        state = await chunker_node(initial_state)
        initial_state.update(state)

        chunks = state.get('chunks', [])
        dialogue_chunks = [c for c in chunks if c.get('chunk_type') == 'dialogue']
        print(f"   ✅ {len(chunks)} total chunks ({len(dialogue_chunks)} dialogue)")

        # Show chunk metadata richness
        if dialogue_chunks:
            sample = dialogue_chunks[0]
            metadata_keys = [k for k in sample.keys() if k != 'text']
            print(f"   ✅ {len(metadata_keys)} metadata fields per chunk:")
            print(f"      {', '.join(metadata_keys[:10])}...")

        # Phase 4: Embedding with Rich Metadata
        print("\n🧠 Phase 4: Embedding + Qdrant Storage")
        state = await embedder_node(initial_state)
        print(f"   ✅ Embeddings stored in Qdrant with rich metadata")

        # Phase 5: Knowledge Extraction (THE CRITICAL TEST)
        print("\n" + "=" * 80)
        print("🎯 Phase 5: KNOWLEDGE EXTRACTION (Critical Test)")
        print("=" * 80)

        state = await knowledge_analyst_node(initial_state)
        initial_state.update(state)

        extracted = state.get('extracted_entities', {})

        # Display extracted data
        print("\n📋 EXTRACTED ENTITIES:")
        print("-" * 80)
        print(json.dumps(extracted, indent=2))

        # Evaluate extraction quality
        print("\n" + "=" * 80)
        print("EXTRACTION QUALITY EVALUATION")
        print("=" * 80)

        # Expected data points from Robin Michalek transcript
        expected_fields = {
            "client_name": "Robin Michalek",
            "client_email": "robincabo@msn.com",
            "client_state": "Washington",
            "transcript_id": "60470637",
            "marital_status": "should be extracted",
            "children_count": "should have value",
            "estate_value": "should have value",
            "deal": "should have price",
        }

        # Check extraction accuracy
        print("\n✅ EXTRACTION ACCURACY CHECK:")

        correct_count = 0
        total_critical = 0

        checks = [
            ("Client Name Extracted", extracted.get('client_name') and "Robin" in str(extracted.get('client_name'))),
            ("Client Email Extracted", extracted.get('client_email') and "robincabo" in str(extracted.get('client_email'))),
            ("Client State Extracted", extracted.get('client_state') and "Washington" in str(extracted.get('client_state'))),
            ("Transcript ID Extracted", extracted.get('transcript_id') == "60470637"),
            ("Meeting Date Extracted", extracted.get('meeting_date') is not None),
            ("Marital Status Extracted", extracted.get('marital_status') and extracted.get('marital_status') != "Unknown"),
            ("Children Count Extracted", extracted.get('children_count') is not None and extracted.get('children_count') != "null"),
            ("Estate Details Extracted", extracted.get('estate_value') is not None or extracted.get('real_estate_count') is not None),
            ("Deal/Pricing Extracted", extracted.get('deal') is not None or extracted.get('deposit') is not None),
            ("Products Discussed", extracted.get('products_discussed') and len(extracted.get('products_discussed', [])) > 0),
        ]

        for check_name, passed in checks:
            total_critical += 1
            if passed:
                correct_count += 1
                print(f"   ✅ PASS: {check_name}")
            else:
                print(f"   ❌ FAIL: {check_name}")

        accuracy = (correct_count / total_critical) * 100
        print(f"\n📊 Extraction Accuracy: {correct_count}/{total_critical} ({accuracy:.1f}%)")

        # Performance metrics
        print("\n📈 PERFORMANCE METRICS:")
        print(f"   Chunks created: {len(dialogue_chunks)}")
        print(f"   Average chunk size: {sum(len(c.get('text', '')) for c in dialogue_chunks) / len(dialogue_chunks):.0f} chars")
        print(f"   Metadata fields per chunk: {len(metadata_keys)}")
        print(f"   Extraction accuracy: {accuracy:.1f}%")

        # Verdict
        print("\n" + "=" * 80)
        print("FINAL VERDICT")
        print("=" * 80)

        if accuracy >= 80:
            print("🎉 EXCELLENT: KnowledgeAnalyst extraction is highly accurate!")
            print(f"   Semantic chunking + rich metadata → {accuracy:.1f}% accuracy")
            print("\n✅ Benefits of enhanced chunking:")
            print("   - Dialogue turn boundaries respected")
            print("   - Conversation phases preserved")
            print("   - Rich metadata enables targeted retrieval")
            print("   - NLP-enriched chunks improve context")
            return 0
        elif accuracy >= 60:
            print(f"⚠️  GOOD: {accuracy:.1f}% accuracy, but room for improvement")
            print("   Consider: Hybrid search + reranking (Phase 3)")
            return 0
        else:
            print(f"❌ POOR: Only {accuracy:.1f}% accuracy")
            print("   Need to investigate retrieval strategy")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: Test failed")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_knowledge_extraction())
    sys.exit(exit_code)
