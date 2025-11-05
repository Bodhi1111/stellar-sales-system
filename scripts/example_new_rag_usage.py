"""
Example: Using the New RAG Architecture

This script demonstrates how to use the optimized RAG system
with intent-based query routing and retrieval strategies.
"""

import asyncio
from config.settings import settings
from core.rag.query_router import QueryRouter
from core.rag.retrieval_engine import RetrievalEngine


async def example_fact_lookup():
    """
    Example 1: Fact Lookup Query
    
    Query: "What was the deal amount?"
    Expected Intent: FACT_LOOKUP
    Expected Strategy: hybrid_keyword_heavy (70% BM25, 30% vector)
    Expected Collections: chunks_detailed, entities
    """
    print("=" * 80)
    print("EXAMPLE 1: FACT LOOKUP QUERY")
    print("=" * 80)
    
    query = "What was the deal amount?"
    print(f"\n🔍 Query: {query}")
    
    # Step 1: Route query
    router = QueryRouter()
    query_plan = await router.route(query)
    
    print(f"\n📋 Query Plan:")
    print(f"   Intent: {query_plan.intent.value}")
    print(f"   Collections: {query_plan.collections}")
    print(f"   Strategy: {query_plan.retrieval_strategy}")
    print(f"   Top-k: {query_plan.top_k}")
    print(f"   Rerank: {query_plan.rerank}")
    print(f"   Use Cache: {query_plan.use_cache}")
    
    # Step 2: Execute retrieval
    engine = RetrievalEngine(settings)
    results = await engine.retrieve(query_plan, query)
    
    print(f"\n✅ Retrieved {len(results)} chunks:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n   Chunk {i}:")
        print(f"      Text: {result['text'][:100]}...")
        print(f"      Score: {result['score']:.4f}")
        print(f"      Phase: {result.get('conversation_phase', 'N/A')}")
        print(f"      Speaker: {result.get('speaker_name', 'N/A')}")
    
    return results


async def example_context_question():
    """
    Example 2: Context Question
    
    Query: "Why did the client hesitate about the trust structure?"
    Expected Intent: CONTEXT_QUESTION
    Expected Strategy: dense_semantic (100% vector)
    Expected Collections: chunks_contextual, chunks_detailed
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: CONTEXT QUESTION")
    print("=" * 80)
    
    query = "Why did the client hesitate about the trust structure?"
    print(f"\n🔍 Query: {query}")
    
    router = QueryRouter()
    query_plan = await router.route(query)
    
    print(f"\n📋 Query Plan:")
    print(f"   Intent: {query_plan.intent.value}")
    print(f"   Collections: {query_plan.collections}")
    print(f"   Strategy: {query_plan.retrieval_strategy}")
    print(f"   Rerank: {query_plan.rerank}")
    
    engine = RetrievalEngine(settings)
    results = await engine.retrieve(query_plan, query)
    
    print(f"\n✅ Retrieved {len(results)} chunks:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n   Chunk {i}:")
        print(f"      Text: {result['text'][:150]}...")
        print(f"      Score: {result['score']:.4f}")
    
    return results


async def example_aggregation_query():
    """
    Example 3: Aggregation Query
    
    Query: "Summarize the main objections discussed"
    Expected Intent: AGGREGATION
    Expected Strategy: hierarchical_summary
    Expected Collections: summaries, chunks_contextual
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: AGGREGATION QUERY")
    print("=" * 80)
    
    query = "Summarize the main objections discussed"
    print(f"\n🔍 Query: {query}")
    
    router = QueryRouter()
    query_plan = await router.route(query)
    
    print(f"\n📋 Query Plan:")
    print(f"   Intent: {query_plan.intent.value}")
    print(f"   Collections: {query_plan.collections}")
    print(f"   Strategy: {query_plan.retrieval_strategy}")
    
    engine = RetrievalEngine(settings)
    results = await engine.retrieve(query_plan, query)
    
    # Hierarchical results
    if isinstance(results, dict):
        print(f"\n✅ Hierarchical Results:")
        print(f"   Summaries: {len(results.get('summaries', []))}")
        print(f"   Details: {len(results.get('details', []))}")
        
        if results.get('summaries'):
            print(f"\n   📄 Summary:")
            summary = results['summaries'][0]
            print(f"      {summary.get('executive_summary', summary.get('text', ''))[:200]}...")
    else:
        print(f"\n✅ Retrieved {len(results)} results")
    
    return results


async def example_filtered_search():
    """
    Example 4: Filtered Search with Metadata
    
    Query: "Show me pricing discussions where the client had concerns"
    Filters: conversation_phase=Pricing, contains_objection=True, speaker_role=Client
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: FILTERED SEARCH")
    print("=" * 80)
    
    query = "Show me pricing discussions where the client had concerns"
    print(f"\n🔍 Query: {query}")
    
    router = QueryRouter()
    
    # Route with explicit context for better filtering
    query_plan = await router.route(
        query,
        context={
            "transcript_id": "12345678",  # Specific transcript
            "focus_phase": "Pricing"
        }
    )
    
    print(f"\n📋 Query Plan:")
    print(f"   Intent: {query_plan.intent.value}")
    print(f"   Collections: {query_plan.collections}")
    print(f"   Filters: {query_plan.filters}")
    
    engine = RetrievalEngine(settings)
    results = await engine.retrieve(query_plan, query)
    
    print(f"\n✅ Retrieved {len(results)} filtered chunks:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n   Chunk {i}:")
        print(f"      Text: {result['text'][:100]}...")
        print(f"      Phase: {result.get('conversation_phase')}")
        print(f"      Speaker: {result.get('speaker_name')}")
        print(f"      Has Objection: {result.get('contains_objection', False)}")
    
    return results


async def compare_old_vs_new():
    """
    Example 5: Performance Comparison
    
    Run same query through old and new systems, compare latency
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: PERFORMANCE COMPARISON")
    print("=" * 80)
    
    query = "What did the client say about pricing?"
    
    import time
    
    # New system
    print(f"\n⚡ NEW RAG System:")
    start = time.time()
    
    router = QueryRouter()
    query_plan = await router.route(query)
    engine = RetrievalEngine(settings)
    new_results = await engine.retrieve(query_plan, query)
    
    new_latency = time.time() - start
    print(f"   Latency: {new_latency*1000:.0f}ms")
    print(f"   Results: {len(new_results)}")
    print(f"   Intent: {query_plan.intent.value}")
    print(f"   Strategy: {query_plan.retrieval_strategy}")
    
    # Old system (simulated - you'd call the actual old RAG here)
    print(f"\n📜 OLD RAG System (simulated):")
    old_latency = 0.35  # Typical old system latency
    old_results_count = 10
    print(f"   Latency: {old_latency*1000:.0f}ms")
    print(f"   Results: {old_results_count}")
    print(f"   Strategy: one-size-fits-all hybrid")
    
    # Comparison
    print(f"\n📊 Comparison:")
    speedup = old_latency / new_latency if new_latency > 0 else 0
    print(f"   ⚡ Speedup: {speedup:.1f}x faster")
    print(f"   🎯 Precision: Intent-based routing")
    print(f"   💰 Cost: Fewer embeddings (query expansion selective)")


async def main():
    """
    Run all examples
    """
    print("\n" + "=" * 80)
    print("NEW RAG ARCHITECTURE - USAGE EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates the new intent-based RAG system.")
    print("Each example shows a different query type and how it's handled.")
    
    try:
        # Example 1: Fact lookup (fast, keyword-heavy)
        await example_fact_lookup()
        
        # Example 2: Context question (semantic, reranked)
        await example_context_question()
        
        # Example 3: Aggregation (hierarchical)
        await example_aggregation_query()
        
        # Example 4: Filtered search (metadata-based)
        await example_filtered_search()
        
        # Example 5: Performance comparison
        await compare_old_vs_new()
        
        print("\n" + "=" * 80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                                                                    ║
    ║     Stellar Sales System - New RAG Architecture Examples          ║
    ║                                                                    ║
    ║  This script demonstrates the optimized RAG system with:          ║
    ║  • Intent-based query routing                                     ║
    ║  • Strategy-specific retrieval                                    ║
    ║  • Metadata filtering                                             ║
    ║  • Performance improvements                                       ║
    ║                                                                    ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
