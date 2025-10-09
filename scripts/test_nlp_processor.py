#!/usr/bin/env python3
"""
Test NLP Processor in isolation.
Verifies that semantic NLP analysis works correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.nlp_processor import get_nlp_processor


def test_nlp_processor():
    """Test NLP processor with sample transcript"""
    print("=" * 80)
    print("TESTING NLP PROCESSOR")
    print("=" * 80)

    # Sample transcript
    sample_transcript = """[00:00:05] Representative: Good morning! Thanks for joining me today.
[00:00:12] Client: Good morning. Happy to be here.
[00:01:30] Representative: Let me introduce myself. I'm John from Estate Planning Solutions.
[00:02:15] Client: Nice to meet you, John.
[00:03:45] Representative: So what brought you to reach out to us today?
[00:04:10] Client: Well, my wife and I have been thinking about estate planning. We want to make sure our kids are taken care of.
[00:05:20] Representative: That's wonderful. Let me walk you through what we'll cover today.
[00:07:15] Representative: We've been helping families like yours for over 20 years.
[00:12:30] Client: What are your main goals for your estate plan?
[00:13:45] Client: We want to avoid probate and make sure everything goes smoothly for our children.
[00:18:45] Representative: Tell me about your current assets.
[00:19:23] Client: We own a house in California worth about $250,000, and my husband has an LLC for his business.
[00:25:10] Representative: Let me explain the difference between a will and a trust.
[00:32:00] Representative: A revocable living trust gives you much more control and privacy.
[00:45:15] Representative: Our comprehensive package is $5,000, which includes the trust, pour-over will, and power of attorney documents.
[00:46:30] Client: That seems expensive. I've seen online services for much less.
[00:47:45] Representative: I understand your concern. Let me explain what makes our service different.
[00:52:30] Client: How long does the process take?
[00:53:15] Representative: Typically 4-6 weeks from signing to completion.
[00:58:00] Representative: So, are you ready to move forward today?
[00:58:45] Client: Yes, I think this makes sense for us.
"""

    print(f"\n📄 Sample Transcript:")
    print(f"   {len(sample_transcript)} characters")
    print(f"   {len(sample_transcript.split('['))} dialogue turns")

    # Get NLP processor
    nlp = get_nlp_processor()

    print("\n🧠 Running NLP Analysis...")
    print("-" * 80)

    # Analyze transcript
    result = nlp.analyze_transcript(sample_transcript)

    # Display results
    print("\n" + "=" * 80)
    print("NLP ANALYSIS RESULTS")
    print("=" * 80)

    # 1. Conversation Phases
    print("\n1️⃣  CONVERSATION PHASES:")
    phases = result.get("conversation_phases", [])
    for i, phase in enumerate(phases, 1):
        print(f"   Phase {i}:")
        print(f"      - Name: {phase.get('phase')}")
        print(f"      - Time: {phase.get('start_timestamp')} → {phase.get('end_timestamp')}")
        print(f"      - Topics: {', '.join(phase.get('key_topics', []))}")
        print()

    # 2. Named Entities
    print("2️⃣  NAMED ENTITIES:")
    entities = result.get("named_entities", {})
    for entity_type, values in entities.items():
        if values:
            print(f"   {entity_type}: {', '.join(values)}")

    # 3. Topics
    print("\n3️⃣  MAIN TOPICS:")
    topics = result.get("topics", [])
    for i, topic in enumerate(topics[:5], 1):
        print(f"   {i}. {topic}")

    # 4. Semantic Turns (sample)
    print("\n4️⃣  SEMANTIC TURN ANALYSIS (first 5 turns):")
    semantic_turns = result.get("semantic_turns", [])
    for turn in semantic_turns[:5]:
        print(f"   [{turn['timestamp']}] {turn['speaker']}:")
        print(f"      - Intent: {turn['intent']}")
        print(f"      - Sentiment: {turn['sentiment']}")
        print(f"      - Discourse: {turn['discourse_marker']}")
        print(f"      - Has entity: {turn['contains_entity']}")
        print()

    # 5. Document Metadata
    print("5️⃣  DOCUMENT METADATA:")
    doc_meta = result.get("document_metadata", {})
    print(f"   Total turns: {doc_meta.get('total_turns')}")
    print(f"   Question count: {doc_meta.get('question_count')}")
    print(f"   Objection count: {doc_meta.get('objection_count')}")
    print(f"   Client engagement: {doc_meta.get('client_engagement')}")
    print(f"   Entities found: {doc_meta.get('entity_count')}")

    print("\n   Intent distribution:")
    for intent, count in doc_meta.get('intent_distribution', {}).items():
        print(f"      - {intent}: {count}")

    print("\n   Sentiment distribution:")
    for sentiment, count in doc_meta.get('sentiment_distribution', {}).items():
        print(f"      - {sentiment}: {count}")

    # 6. Relationships
    print("\n6️⃣  RELATIONSHIPS:")
    relationships = result.get("relationships", [])
    for rel in relationships:
        print(f"   {rel['subject']} → {rel['predicate']} → {rel['object']}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    # Verify critical components
    print("\n✅ VERIFICATION:")
    checks = [
        ("Conversation phases detected", len(phases) > 0),
        ("Entities extracted", any(entities.values())),
        ("Topics identified", len(topics) > 0),
        ("Semantic turns analyzed", len(semantic_turns) > 0),
        ("Document metadata computed", doc_meta.get('total_turns', 0) > 0)
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All NLP components working correctly!")
        return 0
    else:
        print("\n⚠️  Some NLP components failed")
        return 1


if __name__ == "__main__":
    exit_code = test_nlp_processor()
    sys.exit(exit_code)
