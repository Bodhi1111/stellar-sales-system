# RAG Implementation Roadmap
## Practical Step-by-Step Guide for Evolution

**Purpose**: Actionable implementation plan based on RAG Architecture Audit  
**Target**: Transform 50% accuracy to 85%+ through systematic improvements  
**Timeline**: 8-12 weeks  

---

## Quick Reference: Priority Matrix

| Priority | Task | Impact | Effort | Timeline |
|----------|------|--------|--------|----------|
| 🔴 P1 | Enable Semantic NLP | ⭐⭐⭐ High | 🔧 Low | Week 1 |
| 🔴 P2 | Implement Re-ranking | ⭐⭐⭐ High | 🔧🔧 Medium | Week 2 |
| 🔴 P3 | Activate Semantic Chunking | ⭐⭐ Medium-High | 🔧 Low | Week 1 |
| 🟡 P4 | Query Expansion | ⭐⭐ Medium | 🔧🔧 Medium | Week 3 |
| 🟡 P5 | Structured Logging | ⭐ Medium | 🔧🔧 Medium | Week 3 |
| 🟡 P6 | Config Centralization | ⭐ Low-Medium | 🔧🔧 Medium | Week 4 |
| 🟢 P7 | Context Preservation | ⭐⭐ Medium | 🔧🔧🔧 High | Week 5-6 |
| 🟢 P8 | Caching Layer | ⭐⭐ Medium | 🔧🔧🔧 High | Week 6-7 |
| 🟢 P9 | Feedback Loop | ⭐⭐⭐ High | 🔧🔧🔧 High | Week 8-10 |

---

## Phase 1: Quick Wins (Weeks 1-2)
### Goal: Activate existing advanced features, gain 20-25% accuracy improvement

---

### 🔴 Task P1: Enable Semantic NLP Mode

**Current State**: Architecture designed but not enabled  
**Target State**: Semantic NLP active in pipeline  
**Expected Gain**: +15-20% accuracy  

#### Step 1.1: Add Configuration Setting

**File**: `config/settings.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Semantic NLP Configuration (NEW)
    USE_SEMANTIC_NLP: bool = True  # Enable semantic NLP analysis
    EXTRACT_INTENT: bool = True
    EXTRACT_SENTIMENT: bool = True
    EXTRACT_ENTITIES: bool = True
    EXTRACT_TOPICS: bool = True
```

**Test**:
```bash
# Verify settings load correctly
./venv/bin/python -c "from config.settings import settings; print(f'Semantic NLP: {settings.USE_SEMANTIC_NLP}')"
```

---

#### Step 1.2: Update Structuring Node

**File**: `orchestrator/graph.py`

**Current**:
```python
async def structuring_node(state: AgentState):
    """Analyze conversation phases and structure"""
    structured_dialogue = state.get("structured_dialogue")
    conversation_phases = await structuring_agent.run(structured_dialogue=structured_dialogue)
    return {"conversation_phases": conversation_phases}
```

**Updated**:
```python
async def structuring_node(state: AgentState):
    """
    NEW ARCHITECTURE: Runs FIRST on raw transcript
    Performs semantic NLP analysis to identify conversation phases
    """
    content = state["file_path"].read_text(encoding='utf-8')
    
    # Enable semantic NLP analysis based on settings
    result = await structuring_agent.run(
        raw_transcript=content,
        use_semantic_nlp=settings.USE_SEMANTIC_NLP
    )
    
    # Extract components from semantic analysis
    if isinstance(result, dict) and settings.USE_SEMANTIC_NLP:
        return {
            "conversation_phases": result.get("conversation_phases", []),
            "semantic_turns": result.get("semantic_turns", []),
            "key_entities_nlp": result.get("key_entities", {}),
            "conversation_structure": result.get("overall_structure", {})
        }
    else:
        # Backward compatible (list of phases)
        return {"conversation_phases": result}
```

---

#### Step 1.3: Update AgentState

**File**: `orchestrator/state.py`

**Add new fields**:
```python
class AgentState(TypedDict):
    """
    This is the basket that carries our data through the graph.
    """
    # ... existing fields ...
    
    # --- Semantic NLP Outputs (NEW) ---
    semantic_turns: List[Dict[str, Any]]  # Per-turn intent/sentiment
    key_entities_nlp: Dict[str, Any]      # Extracted entities
    conversation_structure: Dict[str, Any]  # Overall metrics
```

---

#### Step 1.4: Update Parser to Enrich Dialogue

**File**: `agents/parser/parser_agent.py`

**Add method**:
```python
def _enrich_with_semantic_data(self, dialogue: List[Dict], semantic_turns: List[Dict]) -> List[Dict]:
    """
    Enrich dialogue turns with semantic metadata (intent, sentiment, etc.)
    """
    if not semantic_turns:
        return dialogue
    
    # Create lookup by timestamp
    semantic_lookup = {turn["timestamp"]: turn for turn in semantic_turns}
    
    # Enrich each dialogue turn
    for turn in dialogue:
        timestamp = turn.get("timestamp")
        if timestamp in semantic_lookup:
            semantic_data = semantic_lookup[timestamp]
            turn["intent"] = semantic_data.get("intent")
            turn["sentiment"] = semantic_data.get("sentiment")
            turn["contains_entity"] = semantic_data.get("contains_entity")
            turn["discourse_marker"] = semantic_data.get("discourse_marker")
    
    return dialogue
```

**Update run() method**:
```python
async def run(self, file_path: Path, semantic_turns: List[Dict] = None) -> List[Dict]:
    # ... existing parsing logic ...
    
    # Enrich with semantic data if available
    if semantic_turns:
        dialogue = self._enrich_with_semantic_data(dialogue, semantic_turns)
    
    return {"structured_dialogue": dialogue, "transcript_id": transcript_id}
```

**Update parser_node**:
```python
async def parser_node(state: AgentState):
    """Parse raw transcript into structured dialogue"""
    result = await parser_agent.run(
        file_path=state.get("file_path"),
        semantic_turns=state.get("semantic_turns")  # Pass semantic data
    )
    return result
```

---

#### Step 1.5: Update Embedder to Store Semantic Metadata

**File**: `agents/embedder/embedder_agent.py`

**Update payload creation**:
```python
def _create_payload(self, chunk: Dict, transcript_id: str, metadata: Dict) -> Dict:
    """Create Qdrant payload with semantic metadata"""
    
    payload = {
        "transcript_id": transcript_id,
        "chunk_index": chunk.get("chunk_index", 0),
        "text": chunk.get("text", ""),
        "doc_type": "transcript_chunk",
        "word_count": len(chunk.get("text", "").split()),
        "created_at": datetime.utcnow().isoformat(),
        
        # Basic metadata
        "conversation_phase": chunk.get("conversation_phase"),
        "speakers": chunk.get("speakers", []),
        "timestamp_start": chunk.get("timestamp_start"),
        "timestamp_end": chunk.get("timestamp_end"),
        "client_name": metadata.get("client_name"),
        "meeting_date": metadata.get("meeting_date"),
        
        # Semantic NLP metadata (NEW)
        "dominant_intent": chunk.get("dominant_intent"),
        "sentiment": chunk.get("sentiment"),
        "key_topics": chunk.get("key_topics", []),
        "contains_entities": chunk.get("contains_entities", False),
        "entity_types": chunk.get("entity_types", []),
    }
    
    return payload
```

---

#### Step 1.6: Test Semantic NLP Pipeline

**Create test script**: `scripts/test_semantic_nlp_pipeline.py`

```python
#!/usr/bin/env python3
"""Test semantic NLP pipeline end-to-end"""

import asyncio
from pathlib import Path
from agents.structuring.structuring_agent import StructuringAgent
from agents.parser.parser_agent import ParserAgent
from config.settings import settings

async def test_semantic_nlp():
    print("=" * 60)
    print("SEMANTIC NLP PIPELINE TEST")
    print("=" * 60)
    
    # Test file
    test_file = Path("data/transcripts/test_sprint01.txt")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    # Step 1: Structuring with semantic NLP
    print("\n1. Running StructuringAgent with semantic NLP...")
    structuring_agent = StructuringAgent(settings)
    raw_text = test_file.read_text()
    
    result = await structuring_agent.run(
        raw_transcript=raw_text,
        use_semantic_nlp=True
    )
    
    if isinstance(result, dict):
        print(f"   ✅ Semantic NLP output:")
        print(f"      - Conversation phases: {len(result.get('conversation_phases', []))}")
        print(f"      - Semantic turns: {len(result.get('semantic_turns', []))}")
        print(f"      - Entity types: {list(result.get('key_entities', {}).keys())}")
        print(f"      - Structure: {result.get('overall_structure', {})}")
        
        # Step 2: Parser enrichment
        print("\n2. Running ParserAgent with semantic enrichment...")
        parser_agent = ParserAgent(settings)
        
        parsed_result = await parser_agent.run(
            file_path=test_file,
            semantic_turns=result.get('semantic_turns', [])
        )
        
        structured_dialogue = parsed_result.get('structured_dialogue', [])
        
        # Check for semantic fields
        enriched_count = sum(1 for turn in structured_dialogue if 'intent' in turn)
        print(f"   ✅ Enriched {enriched_count}/{len(structured_dialogue)} dialogue turns")
        
        # Sample enriched turn
        if enriched_count > 0:
            sample = next(turn for turn in structured_dialogue if 'intent' in turn)
            print(f"\n   Sample enriched turn:")
            print(f"      Speaker: {sample.get('speaker')}")
            print(f"      Intent: {sample.get('intent')}")
            print(f"      Sentiment: {sample.get('sentiment')}")
            print(f"      Contains entity: {sample.get('contains_entity')}")
    else:
        print("   ⚠️ Semantic NLP not enabled (got list instead of dict)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_semantic_nlp())
```

**Run test**:
```bash
chmod +x scripts/test_semantic_nlp_pipeline.py
./venv/bin/python scripts/test_semantic_nlp_pipeline.py
```

**Expected output**:
```
✅ Semantic NLP output:
   - Conversation phases: 12
   - Semantic turns: 89
   - Entity types: ['monetary_values', 'dates', 'locations', 'products_mentioned']
   - Structure: {'total_phases': 12, 'client_engagement': 'high', ...}

✅ Enriched 89/89 dialogue turns

Sample enriched turn:
   Speaker: Client
   Intent: question
   Sentiment: concerned
   Contains entity: true
```

---

### 🔴 Task P2: Activate Semantic Chunking

**Current State**: Fixed-size chunking (1400 chars)  
**Target State**: Semantic-aware chunking  
**Expected Gain**: +10-15% accuracy  

#### Step 2.1: Review Existing Semantic Chunker

**Check if file exists**:
```bash
ls -la core/semantic_chunker.py
```

If it exists, review its implementation. If not, create it.

---

#### Step 2.2: Create/Update Semantic Chunker

**File**: `core/semantic_chunker.py`

```python
"""
Semantic Chunking Strategy

Advantages over fixed-size:
- Preserves conversation turns
- Respects topic boundaries
- Maintains semantic coherence
- Better retrieval quality
"""

from typing import List, Dict, Any
from pathlib import Path


class SemanticChunker:
    def __init__(self, max_chunk_size: int = 1400, overlap_turns: int = 1):
        """
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap_turns: Number of conversation turns to overlap
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_turns = overlap_turns
    
    def chunk_by_conversation_turns(
        self, 
        structured_dialogue: List[Dict[str, Any]],
        conversation_phases: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk by conversation turns, respecting speaker changes and phases.
        
        Strategy:
        1. Group consecutive turns by same phase
        2. Create chunks that don't exceed max_chunk_size
        3. Preserve complete speaker turns (never split mid-turn)
        4. Add overlap_turns for context
        """
        chunks = []
        current_chunk_text = []
        current_chunk_metadata = {
            "speakers": set(),
            "conversation_phase": None,
            "timestamp_start": None,
            "timestamp_end": None,
            "turn_count": 0
        }
        
        # Create phase lookup
        phase_lookup = {}
        if conversation_phases:
            for phase in conversation_phases:
                start = phase.get("start_timestamp")
                if start:
                    phase_lookup[start] = phase.get("phase")
        
        for i, turn in enumerate(structured_dialogue):
            turn_text = f"[{turn.get('timestamp', 'N/A')}] {turn.get('speaker', 'Unknown')}: {turn.get('text', '')}\n\n"
            
            # Check if adding this turn would exceed max size
            current_size = sum(len(t) for t in current_chunk_text)
            
            if current_size + len(turn_text) > self.max_chunk_size and current_chunk_text:
                # Finalize current chunk
                chunk = self._finalize_chunk(
                    current_chunk_text, 
                    current_chunk_metadata,
                    len(chunks)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk_text) - self.overlap_turns)
                current_chunk_text = current_chunk_text[overlap_start:]
                current_chunk_metadata = {
                    "speakers": set(),
                    "conversation_phase": None,
                    "timestamp_start": None,
                    "timestamp_end": None,
                    "turn_count": len(current_chunk_text)
                }
            
            # Add turn to current chunk
            current_chunk_text.append(turn_text)
            current_chunk_metadata["speakers"].add(turn.get("speaker"))
            
            # Update metadata
            if not current_chunk_metadata["timestamp_start"]:
                current_chunk_metadata["timestamp_start"] = turn.get("timestamp")
            current_chunk_metadata["timestamp_end"] = turn.get("timestamp")
            
            # Get phase from lookup or turn
            phase = turn.get("conversation_phase") or phase_lookup.get(turn.get("timestamp"))
            if phase and not current_chunk_metadata["conversation_phase"]:
                current_chunk_metadata["conversation_phase"] = phase
            
            current_chunk_metadata["turn_count"] += 1
            
            # Copy semantic metadata if available
            if "intent" in turn:
                if "intents" not in current_chunk_metadata:
                    current_chunk_metadata["intents"] = []
                current_chunk_metadata["intents"].append(turn["intent"])
            
            if "sentiment" in turn:
                if "sentiments" not in current_chunk_metadata:
                    current_chunk_metadata["sentiments"] = []
                current_chunk_metadata["sentiments"].append(turn["sentiment"])
        
        # Finalize last chunk
        if current_chunk_text:
            chunk = self._finalize_chunk(
                current_chunk_text, 
                current_chunk_metadata,
                len(chunks)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _finalize_chunk(
        self, 
        chunk_text: List[str], 
        metadata: Dict,
        chunk_index: int
    ) -> Dict[str, Any]:
        """Finalize chunk with aggregated metadata"""
        
        # Aggregate intents (most common)
        dominant_intent = None
        if "intents" in metadata and metadata["intents"]:
            from collections import Counter
            intent_counts = Counter(metadata["intents"])
            dominant_intent = intent_counts.most_common(1)[0][0]
        
        # Aggregate sentiments (most common)
        dominant_sentiment = None
        if "sentiments" in metadata and metadata["sentiments"]:
            from collections import Counter
            sentiment_counts = Counter(metadata["sentiments"])
            dominant_sentiment = sentiment_counts.most_common(1)[0][0]
        
        return {
            "text": "".join(chunk_text),
            "chunk_index": chunk_index,
            "chunk_type": "semantic_dialogue",
            "conversation_phase": metadata["conversation_phase"],
            "speakers": list(metadata["speakers"]),
            "timestamp_start": metadata["timestamp_start"],
            "timestamp_end": metadata["timestamp_end"],
            "turn_count": metadata["turn_count"],
            "dominant_intent": dominant_intent,
            "sentiment": dominant_sentiment,
            "word_count": len("".join(chunk_text).split())
        }
```

---

#### Step 2.3: Update ChunkerAgent

**File**: `agents/chunker/chunker.py`

**Update run() method**:
```python
async def run(self, structured_dialogue: List[Dict], conversation_phases: List[Dict] = None) -> List[Dict]:
    """
    Chunk dialogue semantically, preserving conversation turns.
    """
    print(f"🔪 ChunkerAgent: Creating semantic chunks from {len(structured_dialogue)} turns...")
    
    # Use semantic chunking
    from core.semantic_chunker import SemanticChunker
    chunker = SemanticChunker(
        max_chunk_size=self.settings.rag.chunking.chunk_size if hasattr(self.settings, 'rag') else 1400,
        overlap_turns=1
    )
    
    chunks = chunker.chunk_by_conversation_turns(
        structured_dialogue,
        conversation_phases
    )
    
    print(f"   ✅ Created {len(chunks)} semantic chunks")
    print(f"      Average chunk size: {sum(c['word_count'] for c in chunks) / len(chunks):.0f} words")
    
    return {"chunks": chunks}
```

**Update chunker_node**:
```python
async def chunker_node(state: AgentState):
    """Segment content using semantic chunking"""
    result = await chunker_agent.run(
        structured_dialogue=state.get("structured_dialogue"),
        conversation_phases=state.get("conversation_phases")
    )
    return result
```

---

#### Step 2.4: Test Semantic Chunking

**Create test**: `scripts/test_semantic_chunking_v2.py`

```python
#!/usr/bin/env python3
"""Test semantic chunking implementation"""

import asyncio
from pathlib import Path
from agents.parser.parser_agent import ParserAgent
from agents.structuring.structuring_agent import StructuringAgent
from agents.chunker.chunker import ChunkerAgent
from config.settings import settings

async def test_semantic_chunking():
    print("=" * 60)
    print("SEMANTIC CHUNKING TEST")
    print("=" * 60)
    
    test_file = Path("data/transcripts/test_sprint01.txt")
    
    # Step 1: Parse
    parser = ParserAgent(settings)
    parsed = await parser.run(file_path=test_file)
    structured_dialogue = parsed.get("structured_dialogue", [])
    print(f"\n1. Parsed {len(structured_dialogue)} dialogue turns")
    
    # Step 2: Structure
    structuring = StructuringAgent(settings)
    raw_text = test_file.read_text()
    phases_result = await structuring.run(raw_transcript=raw_text)
    phases = phases_result if isinstance(phases_result, list) else phases_result.get("conversation_phases", [])
    print(f"2. Identified {len(phases)} conversation phases")
    
    # Step 3: Semantic Chunking
    chunker = ChunkerAgent(settings)
    chunks_result = await chunker.run(
        structured_dialogue=structured_dialogue,
        conversation_phases=phases
    )
    chunks = chunks_result.get("chunks", [])
    
    print(f"\n3. Created {len(chunks)} semantic chunks")
    
    # Analyze chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3
        print(f"\n   Chunk {i}:")
        print(f"      Size: {chunk['word_count']} words")
        print(f"      Speakers: {chunk['speakers']}")
        print(f"      Phase: {chunk.get('conversation_phase', 'N/A')}")
        print(f"      Turn count: {chunk['turn_count']}")
        print(f"      Intent: {chunk.get('dominant_intent', 'N/A')}")
        print(f"      Sentiment: {chunk.get('sentiment', 'N/A')}")
        print(f"      Preview: {chunk['text'][:150]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_semantic_chunking())
```

---

### 🔴 Task P3: Implement Re-ranking Layer

**Expected Gain**: +10% accuracy  
**Timeline**: Week 2  

#### Step 3.1: Install Cross-Encoder

**Update requirements.txt**:
```txt
# Add cross-encoder for re-ranking
sentence-transformers>=2.2.0
```

**Install**:
```bash
./venv/bin/pip install sentence-transformers -U
```

---

#### Step 3.2: Create RerankerAgent

**File**: `agents/reranker/reranker_agent.py`

```python
"""
Reranker Agent - Cross-Encoder based re-ranking for improved retrieval accuracy

Why re-ranking?
- Vector similarity (bi-encoder) is fast but less accurate
- Cross-encoder processes query+document together for better relevance
- Use bi-encoder for recall (retrieve many), cross-encoder for precision (rank few)

Expected improvement: +10% accuracy
"""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder
from agents.base_agent import BaseAgent
from config.settings import Settings


class RerankerAgent(BaseAgent):
    """
    Re-ranks retrieved chunks using cross-encoder for higher accuracy.
    """
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        
        # Cross-encoder model for re-ranking
        # This model is trained specifically for passage re-ranking
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("   📊 Loaded cross-encoder model for re-ranking")
    
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-rank chunks based on query relevance.
        
        Args:
            data: {
                "query": str,
                "chunks": List[Dict],  # Each with "text" field
                "top_k": int (optional)
            }
        
        Returns:
            {"reranked_chunks": List[Dict]}
        """
        query = data.get("query", "")
        chunks = data.get("chunks", [])
        top_k = data.get("top_k", len(chunks))
        
        if not chunks:
            return {"reranked_chunks": []}
        
        print(f"   🔄 Re-ranking {len(chunks)} chunks...")
        
        # Create query-chunk pairs
        pairs = [[query, chunk.get("text", "")] for chunk in chunks]
        
        # Get relevance scores from cross-encoder
        scores = self.cross_encoder.predict(pairs)
        
        # Sort chunks by score
        ranked_pairs = sorted(
            zip(scores, chunks),
            key=lambda x: x[0],
            reverse=True
        )
        
        # Extract top-k chunks with scores
        reranked_chunks = []
        for score, chunk in ranked_pairs[:top_k]:
            chunk_with_score = chunk.copy()
            chunk_with_score["rerank_score"] = float(score)
            reranked_chunks.append(chunk_with_score)
        
        print(f"   ✅ Re-ranked to top {len(reranked_chunks)} chunks")
        print(f"      Score range: {reranked_chunks[0]['rerank_score']:.3f} → {reranked_chunks[-1]['rerank_score']:.3f}")
        
        return {"reranked_chunks": reranked_chunks}
```

---

#### Step 3.3: Integrate into Knowledge Analyst

**File**: `agents/knowledge_analyst/knowledge_analyst_agent.py`

**Import**:
```python
from agents.reranker.reranker_agent import RerankerAgent
```

**Initialize in __init__**:
```python
def __init__(self, settings: Settings):
    # ... existing code ...
    
    # Initialize reranker
    self.reranker = RerankerAgent(settings)
```

**Update run() method**:
```python
async def run(self, transcript_id: str, file_path: Path) -> Dict[str, Any]:
    print(f"📊 KnowledgeAnalystAgent: Analyzing transcript for {file_path.name}...")
    
    # Step 1: Retrieve chunks (hybrid search)
    chunks = await self._retrieve_with_hybrid_search(transcript_id, top_k=30)  # Retrieve more
    
    if not chunks:
        print("   - No chunks found in Qdrant, skipping analysis.")
        return {"knowledge_graph_status": "skipped", "extracted_entities": {}}
    
    # Step 2: Re-rank chunks (NEW)
    print(f"   🔄 Re-ranking {len(chunks)} chunks for relevance...")
    chunk_dicts = [{"text": chunk} for chunk in chunks]
    reranked_result = await self.reranker.run({
        "query": "Extract sales meeting data: client info, estate details, deal terms",
        "chunks": chunk_dicts,
        "top_k": 15  # Keep top 15 after re-ranking
    })
    
    reranked_chunks = [c["text"] for c in reranked_result.get("reranked_chunks", [])]
    
    # Step 3: Extract facts from re-ranked chunks
    extracted_facts = await self._map_chunks_to_facts(reranked_chunks)
    
    # ... rest of method unchanged ...
```

---

#### Step 3.4: Test Re-ranking

**Create test**: `scripts/test_reranking.py`

```python
#!/usr/bin/env python3
"""Test re-ranking functionality"""

import asyncio
from agents.reranker.reranker_agent import RerankerAgent
from config.settings import settings

async def test_reranking():
    print("=" * 60)
    print("RE-RANKING TEST")
    print("=" * 60)
    
    # Create test chunks
    chunks = [
        {"text": "The client's name is John Smith and his email is john@example.com"},
        {"text": "We discussed various estate planning options for the future"},
        {"text": "The total deal value is $5,000 with a $1,000 deposit"},
        {"text": "The weather was nice today and we had a pleasant conversation"},
        {"text": "John mentioned he has 3 children and is married"},
        {"text": "I love my job and working with clients is rewarding"},
    ]
    
    query = "What is the client's name and contact information?"
    
    print(f"\nQuery: {query}")
    print(f"\nOriginal order:")
    for i, chunk in enumerate(chunks):
        print(f"  {i+1}. {chunk['text'][:60]}...")
    
    # Re-rank
    reranker = RerankerAgent(settings)
    result = await reranker.run({
        "query": query,
        "chunks": chunks,
        "top_k": 3
    })
    
    reranked = result.get("reranked_chunks", [])
    
    print(f"\nRe-ranked order (top 3):")
    for i, chunk in enumerate(reranked):
        score = chunk.get("rerank_score", 0)
        print(f"  {i+1}. [Score: {score:.3f}] {chunk['text'][:60]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_reranking())
```

**Expected output**:
```
Re-ranked order (top 3):
  1. [Score: 12.543] The client's name is John Smith and his email is john@...
  2. [Score: 8.123] John mentioned he has 3 children and is married
  3. [Score: 2.456] The total deal value is $5,000 with a $1,000 deposit
```

---

## Phase 1 Checklist

- [ ] **P1: Enable Semantic NLP**
  - [ ] Add settings configuration
  - [ ] Update structuring_node
  - [ ] Update AgentState
  - [ ] Update ParserAgent
  - [ ] Update EmbedderAgent
  - [ ] Test end-to-end

- [ ] **P2: Activate Semantic Chunking**
  - [ ] Create/review SemanticChunker
  - [ ] Update ChunkerAgent
  - [ ] Update chunker_node
  - [ ] Test chunking quality

- [ ] **P3: Implement Re-ranking**
  - [ ] Install cross-encoder
  - [ ] Create RerankerAgent
  - [ ] Integrate into KnowledgeAnalyst
  - [ ] Test re-ranking accuracy

**Phase 1 Success Metrics**:
- [ ] Semantic NLP active and producing enriched metadata
- [ ] Semantic chunks preserve conversation turns
- [ ] Re-ranking improves chunk relevance
- [ ] Overall accuracy: 50% → 70%+ (target: 75%)

---

## Phase 2: Infrastructure Improvements (Weeks 3-4)

### 🟡 Task P4: Query Expansion

**File**: `core/query_expander.py`

```python
"""Query expansion for better retrieval coverage"""

from typing import List
import requests
from config.settings import Settings


class QueryExpander:
    """
    Expands queries using:
    1. LLM-based paraphrasing
    2. Domain-specific synonyms
    3. Query decomposition
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Domain-specific synonym mappings
        self.domain_synonyms = {
            "trust": ["revocable living trust", "irrevocable trust", "testamentary trust", "living trust"],
            "will": ["last will", "testament", "pour-over will", "living will"],
            "estate": ["estate planning", "estate value", "assets", "wealth"],
            "property": ["real estate", "house", "home", "land", "LLC"],
            "client": ["customer", "buyer", "prospect"],
            "objection": ["concern", "hesitation", "worry", "doubt"],
        }
    
    def expand_with_synonyms(self, query: str) -> List[str]:
        """Add domain-specific synonyms"""
        expanded = [query]
        
        query_lower = query.lower()
        for term, synonyms in self.domain_synonyms.items():
            if term in query_lower:
                for synonym in synonyms:
                    expanded.append(query.replace(term, synonym))
        
        return list(set(expanded))  # Remove duplicates
    
    def expand_with_llm(self, query: str, num_variations: int = 2) -> List[str]:
        """Generate query variations using LLM"""
        prompt = f"""Generate {num_variations} alternative ways to ask this question:

Original: {query}

Alternatives (one per line):
1."""
        
        try:
            response = requests.post(
                self.settings.OLLAMA_API_URL,
                json={
                    "model": self.settings.LLM_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            variations_text = response.json().get("response", "")
            variations = [
                v.strip("1234567890. ") 
                for v in variations_text.split("\n") 
                if v.strip()
            ]
            
            return [query] + variations[:num_variations]
        except Exception as e:
            print(f"   ⚠️ LLM expansion failed: {e}")
            return [query]
```

**Integration into KnowledgeAnalyst**:
```python
from core.query_expander import QueryExpander

# In __init__:
self.query_expander = QueryExpander(settings)

# In retrieval method:
base_queries = [
    "client name email address phone",
    "estate value assets real estate"
]

# Expand queries
expanded_queries = []
for query in base_queries:
    expanded_queries.extend(self.query_expander.expand_with_synonyms(query))

# Use expanded queries for retrieval
```

---

### 🟡 Task P5: Structured Logging

**File**: `core/logger.py`

```python
"""Structured logging configuration for the entire system"""

import logging
import sys
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Add colors to console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        record.levelname = f"{log_color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_dir: Path = None,
    console: bool = True
):
    """
    Setup structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files (None = no file logging)
        console: Whether to log to console
    """
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(colored_formatter)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    # File handler
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"stellar_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, file_logging={log_dir is not None}")
    
    return logger
```

**Update agents to use logging**:
```python
import logging

class KnowledgeAnalystAgent(BaseAgent):
    def __init__(self, settings):
        super().__init__(settings)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def run(self, ...):
        self.logger.info(f"Starting analysis for {file_path.name}")
        self.logger.debug(f"Retrieved {len(chunks)} chunks")
        # Replace all print() with self.logger.info/debug/warning/error
```

---

## Phase 3: Advanced Features (Weeks 5-8)

[Content for remaining tasks P6-P9 would follow similar detailed format]

---

## Testing Strategy

### Unit Tests
```bash
# Test individual components
pytest tests/agents/test_reranker.py
pytest tests/core/test_semantic_chunker.py
pytest tests/core/test_query_expander.py
```

### Integration Tests
```bash
# Test full pipeline
python scripts/test_pipeline_with_semantic_nlp.py
```

### Accuracy Evaluation
```bash
# Compare before/after
python scripts/evaluate_extraction_accuracy.py
```

---

## Success Metrics

### Quantitative
- Extraction accuracy: 50% → 85%
- Retrieval precision@10: → 90%
- Processing time: Maintain or improve
- Field completion rate: → 95%

### Qualitative
- Fewer extraction errors in logs
- Better chunk coherence
- More consistent entity extraction
- Improved user satisfaction

---

## Rollback Plan

If any phase causes issues:

1. **Disable feature via settings**:
```python
USE_SEMANTIC_NLP = False
USE_RERANKING = False
USE_SEMANTIC_CHUNKING = False
```

2. **Revert to previous commit**:
```bash
git log --oneline  # Find last good commit
git revert <commit-hash>
```

3. **Run baseline tests**:
```bash
python scripts/test_pipeline_baseline.py
```

---

## End of Roadmap

**Next Steps**: Begin with Phase 1, Task P1. Test thoroughly at each step!
