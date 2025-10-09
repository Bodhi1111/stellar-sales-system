#!/usr/bin/env python3
"""
Direct test of hybrid search retrieval from Qdrant.
Assumes Robin Michalek transcript is already embedded in Qdrant.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.knowledge_analyst.knowledge_analyst_agent import KnowledgeAnalystAgent
from config.settings import settings


async def test_hybrid_retrieval():
    """Test hybrid search retrieval with Robin Michalek transcript"""
    print("=" * 80)
    print("TESTING HYBRID SEARCH RETRIEVAL FROM QDRANT")
    print("=" * 80)

    # Initialize agent
    print("\n🔧 Initializing KnowledgeAnalystAgent...")
    agent = KnowledgeAnalystAgent(settings)

    # Robin Michalek transcript ID
    transcript_id = "60470637"

    print(f"\n📊 Transcript ID: {transcript_id}")
    print(f"🔍 Testing hybrid search retrieval (BM25 + Vector + RRF)...\n")

    try:
        # Test hybrid search retrieval
        chunks = await agent._retrieve_with_hybrid_search(transcript_id, top_k=15)

        print("\n" + "=" * 80)
        print(f"RETRIEVAL RESULTS: {len(chunks)} chunks retrieved")
        print("=" * 80)

        if not chunks:
            print("❌ No chunks retrieved - check if transcript is in Qdrant")
            return 1

        # Display first 3 chunks
        print("\n📄 Sample Retrieved Chunks (first 3):")
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n--- Chunk {i} ---")
            if i == 1:
                # Show full header for verification
                print(chunk[:300])
            else:
                preview = chunk[:200].replace('\n', ' ')
                print(f"{preview}...")

        print("\n" + "=" * 80)
        print("CHUNK COVERAGE ANALYSIS")
        print("=" * 80)

        # Check if critical information is in retrieved chunks
        all_text = " ".join(chunks).lower()

        coverage_checks = [
            ("Client Name (Robin)", "robin" in all_text or "michalek" in all_text),
            ("Email (robincabo)", "robincabo" in all_text or "@msn.com" in all_text),
            ("State (Washington)", "washington" in all_text),
            ("Transcript ID (60470637)", "60470637" in all_text),
            ("Family (daughter/grandchildren)", "daughter" in all_text or "grandchildren" in all_text),
            ("Pricing ($)", "$" in all_text or "price" in all_text or "cost" in all_text),
            ("Estate/Assets", "estate" in all_text or "asset" in all_text or "property" in all_text),
            ("Trust/Will Products", "trust" in all_text or "will" in all_text),
        ]

        print("\n✅ COVERAGE CHECK:")
        covered_count = 0
        for check_name, covered in coverage_checks:
            if covered:
                covered_count += 1
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: NOT FOUND")

        coverage_pct = (covered_count / len(coverage_checks)) * 100
        print(f"\n📊 Coverage: {covered_count}/{len(coverage_checks)} ({coverage_pct:.1f}%)")

        if coverage_pct >= 75:
            print("\n🎉 EXCELLENT: Hybrid search is retrieving comprehensive chunks!")
            print("   Expected extraction accuracy: 75-85%")
        elif coverage_pct >= 60:
            print("\n⚠️  GOOD: Hybrid search is retrieving most critical data")
            print(f"   Expected extraction accuracy: ~{coverage_pct:.0f}%")
        else:
            print("\n❌ POOR: Hybrid search not retrieving enough critical information")
            print("   Need to investigate retrieval strategy")

        return 0 if coverage_pct >= 60 else 1

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_hybrid_retrieval())
    sys.exit(exit_code)
