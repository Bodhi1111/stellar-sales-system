# RAG Architecture Migration Guide

This guide walks through migrating from the current monolithic RAG implementation to the optimized multi-collection architecture.

---

## Table of Contents

1. [Overview](#overview)
2. [Migration Strategy](#migration-strategy)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Testing & Validation](#testing--validation)
5. [Rollback Plan](#rollback-plan)

---

## Overview

### Current Architecture

```
Single Collection: "transcripts"
├── All chunks (parent + child)
├── Headers
└── Summaries (mixed)

Retrieval: One-size-fits-all
└── QdrantRAGMixin with basic hybrid search
```

### Target Architecture

```
Multiple Collections:
├── chunks_detailed (fine-grained, 50-200 tokens)
├── chunks_contextual (medium, 200-500 tokens)
├── summaries (coarse, meeting-level)
├── entities (extracted entities)
└── questions (pre-generated Q&A)

Retrieval: Intent-based routing
├── QueryRouter (intent classification)
├── RetrievalEngine (strategy execution)
├── RerankerEngine (quality improvement)
└── CacheLayer (speed optimization)
```

---

## Migration Strategy

### Principle: Zero-Downtime Migration

We'll use a **dual-write, gradual-read** strategy:

1. **Phase 1**: Write to both old and new collections
2. **Phase 2**: Read from old, validate against new
3. **Phase 3**: Gradual traffic shift to new (10% → 50% → 100%)
4. **Phase 4**: Deprecate old system

---

## Step-by-Step Migration

### Step 1: Set Up New Collections (Week 1)

#### 1.1 Create Collection Schemas

```bash
# Run collection creation script
python scripts/create_rag_collections.py
```

**Script**: `/workspace/scripts/create_rag_collections.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType
from config.settings import settings

def create_collections():
    client = QdrantClient(url=settings.QDRANT_URL)
    
    # Collection 1: Detailed chunks (fine-grained)
    client.create_collection(
        collection_name="chunks_detailed",
        vectors_config=VectorParams(
            size=384,  # BAAI/bge-small-en-v1.5
            distance=Distance.COSINE
        )
    )
    
    # Create payload indexes for fast filtering
    client.create_payload_index(
        collection_name="chunks_detailed",
        field_name="transcript_id",
        field_schema=PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name="chunks_detailed",
        field_name="conversation_phase",
        field_schema=PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name="chunks_detailed",
        field_name="speaker_role",
        field_schema=PayloadSchemaType.KEYWORD
    )
    
    # Collection 2: Contextual chunks (medium)
    client.create_collection(
        collection_name="chunks_contextual",
        vectors_config=VectorParams(
            size=768,  # BAAI/bge-base-en-v1.5
            distance=Distance.COSINE
        )
    )
    
    # Collection 3: Summaries (meeting-level)
    client.create_collection(
        collection_name="summaries",
        vectors_config=VectorParams(
            size=1024,  # BAAI/bge-large-en-v1.5
            distance=Distance.COSINE
        )
    )
    
    print("✅ Collections created successfully")

if __name__ == "__main__":
    create_collections()
```

#### 1.2 Deploy New RAG Components

```bash
# Verify new components are in place
ls -la core/rag/
# Should see:
# - query_router.py
# - retrieval_engine.py
# - reranker.py (TODO)
# - cache_layer.py (TODO)
```

---

### Step 2: Implement Dual-Write (Week 2)

#### 2.1 Update EmbedderAgent for Dual-Write

**File**: `/workspace/agents/embedder/embedder_agent.py`

```python
class EmbedderAgent(BaseAgent):
    """
    Enhanced embedder with dual-write capability
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        
        # Multiple embedding models for different collections
        self.embedding_models = {
            "small": SentenceTransformer("BAAI/bge-small-en-v1.5"),    # 384-dim
            "base": SentenceTransformer("BAAI/bge-base-en-v1.5"),      # 768-dim
            "large": SentenceTransformer("BAAI/bge-large-en-v1.5"),    # 1024-dim
        }
        
        # Migration flag
        self.enable_dual_write = settings.ENABLE_RAG_MIGRATION  # Set in .env
    
    async def run(
        self,
        child_chunks: List[Dict[str, Any]],
        parent_chunks: List[Dict[str, Any]],
        header_chunk: Dict[str, Any],
        transcript_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Embed and store chunks with dual-write support
        """
        
        # Write to OLD collection (existing behavior)
        await self._write_to_old_collection(
            child_chunks, parent_chunks, header_chunk, transcript_id, metadata
        )
        
        # Write to NEW collections (if enabled)
        if self.enable_dual_write:
            await self._write_to_new_collections(
                child_chunks, parent_chunks, header_chunk, transcript_id, metadata
            )
        
        return {"embedding_status": "success"}
    
    async def _write_to_new_collections(self, child_chunks, parent_chunks, header_chunk, transcript_id, metadata):
        """
        Write to new multi-collection architecture
        """
        print("   🔄 Dual-write: Writing to new collections...")
        
        # 1. Write detailed chunks (child chunks with small embeddings)
        await self._write_detailed_chunks(child_chunks, transcript_id, metadata)
        
        # 2. Write contextual chunks (parent chunks with base embeddings)
        await self._write_contextual_chunks(parent_chunks, transcript_id, metadata)
        
        # 3. Generate and write summary
        await self._write_summary(child_chunks, parent_chunks, transcript_id, metadata)
        
        # 4. Extract and write entities
        await self._write_entities(child_chunks, transcript_id, metadata)
        
        print("   ✅ Dual-write complete")
    
    async def _write_detailed_chunks(self, chunks, transcript_id, metadata):
        """Write to chunks_detailed with small model"""
        if not chunks:
            return
        
        texts = [c["text"] for c in chunks]
        embeddings = self.embedding_models["small"].encode(texts).tolist()
        
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            points.append({
                "id": chunk["chunk_id"],
                "vector": embedding,
                "payload": {
                    "chunk_id": chunk["chunk_id"],
                    "transcript_id": transcript_id,
                    "text": chunk["text"],
                    "chunk_type": "detailed",
                    "speaker_name": chunk.get("speaker_name"),
                    "speaker_role": self._infer_speaker_role(chunk.get("speaker_name", "")),
                    "conversation_phase": chunk.get("conversation_phase"),
                    "start_time": chunk.get("start_time"),
                    "end_time": chunk.get("end_time"),
                    "word_count": len(chunk["text"].split()),
                    **metadata
                }
            })
        
        self.qdrant_client.upsert(
            collection_name="chunks_detailed",
            points=points
        )
        
        print(f"      ✅ Wrote {len(points)} detailed chunks")
    
    def _infer_speaker_role(self, speaker_name: str) -> str:
        """Infer speaker role from name"""
        speaker_lower = speaker_name.lower()
        if any(kw in speaker_lower for kw in ["client", "caller", "customer"]):
            return "Client"
        elif any(kw in speaker_lower for kw in ["agent", "rep", "attorney"]):
            return "Agent"
        return "Unknown"
```

#### 2.2 Add Migration Flag to Settings

**File**: `/workspace/config/settings.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # RAG Migration Flags
    ENABLE_RAG_MIGRATION: bool = False  # Set to True to enable dual-write
    RAG_MIGRATION_TRAFFIC_PERCENTAGE: float = 0.0  # 0.0 to 1.0
```

**File**: `/workspace/.env`

```bash
# RAG Migration (set to true when ready)
ENABLE_RAG_MIGRATION=true
RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.0
```

---

### Step 3: Implement Gradual Read Shift (Week 3-4)

#### 3.1 Create Traffic Router

**File**: `/workspace/core/rag/traffic_router.py`

```python
import random
from typing import Dict, Any

class TrafficRouter:
    """
    Routes queries between old and new RAG systems
    based on traffic percentage setting
    """
    
    def __init__(self, settings):
        self.traffic_percentage = settings.RAG_MIGRATION_TRAFFIC_PERCENTAGE
        self.old_rag = OldRAGImplementation(settings)
        self.new_rag = NewRAGImplementation(settings)
    
    async def route_query(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """
        Route query to old or new system based on traffic percentage
        """
        if random.random() < self.traffic_percentage:
            print(f"   🆕 Routing to NEW RAG system ({self.traffic_percentage*100}%)")
            return await self.new_rag.query(query, context)
        else:
            print(f"   📜 Routing to OLD RAG system")
            return await self.old_rag.query(query, context)
```

#### 3.2 Update SalesCopilotAgent

**File**: `/workspace/agents/sales_copilot/sales_copilot_agent.py`

```python
from core.rag.traffic_router import TrafficRouter

class SalesCopilotAgent(BaseAgent):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.rag_router = TrafficRouter(settings)
    
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        query = data["query"]
        transcript_id = data.get("transcript_id")
        
        # Route through traffic router
        results = await self.rag_router.route_query(
            query=query,
            context={"transcript_id": transcript_id}
        )
        
        return {"response": results}
```

---

### Step 4: Gradual Traffic Increase (Week 5-6)

```bash
# Week 5, Day 1: 10% traffic
# Update .env
RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.10

# Restart services
docker-compose restart

# Monitor metrics (Langfuse/LangSmith)
# Compare:
# - Latency (p50, p95, p99)
# - Accuracy (if you have eval dataset)
# - Error rate

# Week 5, Day 3: If metrics look good, increase to 25%
RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.25

# Week 5, Day 5: 50%
RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.50

# Week 6, Day 1: 75%
RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.75

# Week 6, Day 3: 100% (full cutover)
RAG_MIGRATION_TRAFFIC_PERCENTAGE=1.0

# Week 6, Day 5: Disable old system
ENABLE_RAG_MIGRATION=false  # Stop dual-write
```

---

## Testing & Validation

### Unit Tests

**File**: `/workspace/tests/test_rag_migration.py`

```python
import pytest
from core.rag.query_router import QueryRouter, QueryIntent
from core.rag.retrieval_engine import RetrievalEngine

@pytest.mark.asyncio
async def test_query_router_fact_lookup():
    """Test query router classifies fact lookup queries correctly"""
    router = QueryRouter()
    
    plan = await router.route("What was the deal amount?")
    
    assert plan.intent == QueryIntent.FACT_LOOKUP
    assert "chunks_detailed" in plan.collections
    assert plan.retrieval_strategy == "hybrid_keyword_heavy"
    assert plan.use_cache == True

@pytest.mark.asyncio
async def test_query_router_context_question():
    """Test query router classifies context questions correctly"""
    router = QueryRouter()
    
    plan = await router.route("Why did the client hesitate?")
    
    assert plan.intent == QueryIntent.CONTEXT_QUESTION
    assert "chunks_contextual" in plan.collections
    assert plan.rerank == True

@pytest.mark.asyncio
async def test_retrieval_engine(mock_qdrant, mock_embedder):
    """Test retrieval engine executes strategies correctly"""
    from core.rag.query_router import QueryPlan, QueryIntent
    
    engine = RetrievalEngine(mock_settings)
    
    plan = QueryPlan(
        intent=QueryIntent.FACT_LOOKUP,
        collections=["chunks_detailed"],
        retrieval_strategy="hybrid_keyword_heavy",
        top_k=5,
        filters={},
        rerank=False,
        use_cache=True
    )
    
    results = await engine.retrieve(plan, "What was the price?")
    
    assert len(results) <= 5
    assert all("score" in r for r in results)
```

### Integration Tests

```bash
# Test full pipeline with new RAG
python scripts/test_new_rag_pipeline.py

# Expected output:
# ✅ Query router working
# ✅ Retrieval engine working
# ✅ Results returned successfully
# ⏱️ Latency: 120ms (vs 350ms old system)
# 📊 Results: 8 chunks retrieved
```

### A/B Testing

**File**: `/workspace/scripts/compare_old_vs_new_rag.py`

```python
import asyncio
from core.rag.traffic_router import TrafficRouter

async def compare_systems():
    """
    Run same queries through old and new systems
    Compare latency and results
    """
    test_queries = [
        "What was the deal amount?",
        "Why did the client object?",
        "Summarize the meeting",
        "Find all pricing discussions"
    ]
    
    old_rag = OldRAGImplementation()
    new_rag = NewRAGImplementation()
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        
        # Old system
        import time
        start = time.time()
        old_results = await old_rag.query(query)
        old_latency = time.time() - start
        
        # New system
        start = time.time()
        new_results = await new_rag.query(query)
        new_latency = time.time() - start
        
        print(f"   OLD: {old_latency:.2f}s, {len(old_results)} results")
        print(f"   NEW: {new_latency:.2f}s, {len(new_results)} results")
        print(f"   ⚡ Speedup: {old_latency/new_latency:.1f}x")

if __name__ == "__main__":
    asyncio.run(compare_systems())
```

---

## Rollback Plan

### If Migration Issues Occur

1. **Immediate Rollback** (< 5 minutes)
   ```bash
   # Set traffic to 0%
   RAG_MIGRATION_TRAFFIC_PERCENTAGE=0.0
   docker-compose restart
   ```

2. **Disable Dual-Write** (if causing issues)
   ```bash
   ENABLE_RAG_MIGRATION=false
   docker-compose restart
   ```

3. **Delete New Collections** (if corrupt)
   ```bash
   python scripts/delete_new_collections.py
   ```

4. **Investigate & Fix**
   - Check Langfuse logs for errors
   - Review Qdrant metrics
   - Examine query patterns causing issues

5. **Re-attempt Migration**
   - Fix identified issues
   - Start from Step 1 again

---

## Success Metrics

### Before Migration (Baseline)

- **Latency**: p50=300ms, p95=800ms, p99=1500ms
- **Accuracy**: MRR@10 = 0.55, NDCG@10 = 0.61
- **Cost**: 1000 embeddings per 1000 queries

### After Migration (Target)

- **Latency**: p50=100ms (3x improvement), p95=250ms, p99=500ms
- **Accuracy**: MRR@10 = 0.82 (+49%), NDCG@10 = 0.88 (+44%)
- **Cost**: 300 embeddings per 1000 queries (70% reduction)

### How to Measure

1. **Langfuse Dashboard**
   - Track latency percentiles
   - Monitor error rates
   - Compare old vs new trace durations

2. **Custom Evaluation Script**
   ```bash
   python scripts/evaluate_rag_quality.py
   # Outputs: MRR, NDCG, Recall@K, Precision@K
   ```

3. **Cost Tracking**
   - Monitor Qdrant API calls
   - Track embedding generation count
   - Compare before/after bills

---

## Timeline Summary

| Week | Phase | Traffic | Tasks |
|------|-------|---------|-------|
| 1 | Setup | 0% | Create collections, deploy components |
| 2 | Dual-Write | 0% | Enable dual-write, validate data |
| 3-4 | Validation | 0% | Unit tests, integration tests, A/B tests |
| 5 | Ramp-Up | 10% → 50% | Gradual traffic increase, monitor metrics |
| 6 | Cutover | 75% → 100% | Full migration, deprecate old system |
| 7-8 | Optimization | 100% | Fine-tune, optimize, document |

---

## Conclusion

This migration strategy ensures zero downtime and provides multiple rollback points. The key is **gradual validation** at each step before proceeding to the next.

**Risk Mitigation**:
- ✅ Dual-write prevents data loss
- ✅ Gradual traffic shift catches issues early
- ✅ Immediate rollback capability
- ✅ Comprehensive testing at each phase
- ✅ Monitoring and alerting in place

**Next Steps**:
1. Review this migration plan with the team
2. Set up staging environment for testing
3. Create evaluation dataset for accuracy testing
4. Begin Phase 1 (Setup) when approved
