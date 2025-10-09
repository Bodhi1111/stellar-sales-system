# Semantic NLP Architecture - Intelligence First Pipeline

## Overview

The **StructuringAgent** now performs comprehensive **Semantic NLP Analysis** as the FIRST step in the pipeline. This analysis extracts rich linguistic and contextual metadata that enriches every downstream component.

## Where Semantic NLP Analysis Happens

### Location: `agents/structuring/structuring_agent.py`

The StructuringAgent runs **before** parsing and performs two types of analysis:

#### 1. Standard Mode (Current - Backward Compatible)
- Identifies conversation phases with timestamps
- Returns: `List[Dict]` with phase metadata
- Prompt: `_construct_prompt()`

#### 2. Semantic NLP Mode (NEW - Enhanced Metadata)
- **Intent Detection**: Classifies each turn (question, statement, objection, agreement, proposal, clarification)
- **Sentiment Analysis**: Identifies emotional tone (positive, neutral, negative, concerned, excited)
- **Entity Recognition**: Extracts monetary values, dates, locations, products mentioned
- **Discourse Markers**: Identifies transitions, confirmations, hedges, emphasis
- **Topic Modeling**: Key topics discussed per phase
- **Conversation Structure**: Overall metrics (engagement level, objection count, question count)

Returns:
```python
{
  "conversation_phases": [
    {
      "phase": "client's estate details",
      "start_timestamp": "00:18:45",
      "end_timestamp": "00:25:10",
      "dominant_speaker": "Client",
      "key_topics": ["real estate", "California property", "LLC ownership"],
      "sentiment": "positive"
    }
  ],
  "semantic_turns": [
    {
      "timestamp": "00:19:23",
      "speaker": "Client",
      "intent": "statement",
      "sentiment": "neutral",
      "contains_entity": true,
      "discourse_marker": "none"
    }
  ],
  "key_entities": {
    "monetary_values": ["$250,000", "$5,000 deposit"],
    "dates": ["next Tuesday", "December 15"],
    "locations": ["California", "San Diego County"],
    "products_mentioned": ["revocable living trust", "pour-over will", "power of attorney"]
  },
  "overall_structure": {
    "total_phases": 12,
    "client_engagement": "high",
    "objections_count": 2,
    "questions_count": 15
  }
}
```

Prompt: `_construct_semantic_nlp_prompt()`

## Metadata Enrichment Flow

### Step 1: StructuringAgent (FIRST - Raw Transcript)
**Input**: Raw transcript text
**Process**: Semantic NLP analysis via LLM
**Output**: Rich metadata structure

**Metadata Extracted**:
- Conversation phases with topic/sentiment
- Per-turn intent and sentiment
- Named entities (money, dates, locations, products)
- Discourse structure

**Stored in AgentState**:
- `conversation_phases`: Phase metadata
- `semantic_turns`: Turn-level metadata
- `key_entities_nlp`: Extracted entities
- `conversation_structure`: Overall metrics

---

### Step 2: ParserAgent (Enriches Dialogue Turns)
**Input**: Raw transcript + `conversation_phases` from Step 1
**Process**: Parse dialogue and enrich each turn with phase metadata

**Enrichment**:
```python
{
  "timestamp": "00:19:23",
  "speaker": "Client",
  "text": "We own a house in California worth about $250,000.",
  "conversation_phase": "client's estate details"  # ← FROM STRUCTURING
}
```

**Additional Enhancement** (if semantic NLP enabled):
```python
{
  "timestamp": "00:19:23",
  "speaker": "Client",
  "text": "We own a house in California worth about $250,000.",
  "conversation_phase": "client's estate details",
  "intent": "statement",           # ← FROM SEMANTIC_TURNS
  "sentiment": "neutral",           # ← FROM SEMANTIC_TURNS
  "contains_entity": true,          # ← FROM SEMANTIC_TURNS
  "discourse_marker": "none"        # ← FROM SEMANTIC_TURNS
}
```

---

### Step 3: ChunkerAgent (Creates Metadata-Rich Chunks)
**Input**: Enriched dialogue from Step 2
**Process**: Create semantic chunks with embedded metadata

**Chunk Structure**:
```python
{
  "text": "[00:18:45] Client: We own a house... [full chunk text]",
  "chunk_type": "dialogue",
  "conversation_phase": "client's estate details",    # ← FROM PARSER
  "speakers": ["Client", "Representative"],
  "timestamp_start": "00:18:45",
  "timestamp_end": "00:25:10",

  # ENHANCED METADATA (if semantic NLP enabled):
  "dominant_intent": "statement",                     # ← FROM SEMANTIC_TURNS
  "sentiment": "positive",                            # ← FROM PHASE METADATA
  "key_topics": ["real estate", "California property"], # ← FROM PHASE METADATA
  "contains_entities": true,                          # ← FROM SEMANTIC_TURNS
  "entity_types": ["monetary_values", "locations"]    # ← FROM KEY_ENTITIES_NLP
}
```

---

### Step 4: EmbedderAgent (Stores Rich Metadata in Qdrant)
**Input**: Metadata-rich chunks from Step 3
**Process**: Generate embeddings and store with ALL metadata

**Qdrant Payload** (per chunk):
```python
{
  "transcript_id": "12345678",
  "chunk_index": 15,
  "text": "[full chunk text]",
  "doc_type": "transcript_chunk",
  "word_count": 150,
  "created_at": "2025-10-08T19:00:00Z",

  # BASIC METADATA (current):
  "conversation_phase": "client's estate details",
  "speakers": ["Client", "Representative"],
  "timestamp_start": "00:18:45",
  "timestamp_end": "00:25:10",
  "client_name": "John Doe",
  "meeting_date": "2025-10-07T17:00:00Z",

  # SEMANTIC NLP METADATA (enhanced):
  "dominant_intent": "statement",
  "sentiment": "positive",
  "key_topics": ["real estate", "California property", "LLC ownership"],
  "contains_entities": true,
  "entity_types": ["monetary_values", "locations"],
  "client_engagement": "high"
}
```

**Benefits**:
- **Targeted Retrieval**: Filter by intent (only retrieve objections, questions, etc.)
- **Sentiment-Based Search**: Find positive/negative segments
- **Entity-Aware Search**: Retrieve chunks with specific entity types
- **Topic Filtering**: Get chunks discussing specific topics

---

### Step 5: KnowledgeAnalystAgent (RAG-Based Extraction)
**Input**: Transcript ID
**Process**: Query Qdrant with semantic filters for highly accurate retrieval

**Enhanced Retrieval Strategies**:

1. **Phase-Based Filtering**:
```python
# Get chunks from specific conversation phases
filter = FieldCondition(
    key="conversation_phase",
    match=MatchAny(any=["client's estate details", "client's goals"])
)
```

2. **Intent-Based Filtering**:
```python
# Get only chunks where client asked questions
filter = FieldCondition(
    key="dominant_intent",
    match=MatchValue(value="question")
)
```

3. **Sentiment-Based Filtering**:
```python
# Get chunks with negative sentiment (potential objections)
filter = FieldCondition(
    key="sentiment",
    match=MatchValue(value="negative")
)
```

4. **Entity-Based Filtering**:
```python
# Get chunks containing monetary values
filter = FieldCondition(
    key="entity_types",
    match=MatchAny(any=["monetary_values"])
)
```

5. **Topic-Based Filtering**:
```python
# Get chunks discussing trusts
filter = FieldCondition(
    key="key_topics",
    match=MatchAny(any=["revocable living trust"])
)
```

**Result**: Highly accurate data extraction with minimal LLM calls and better context.

---

## Enabling Semantic NLP Mode

### Option 1: Enable in Orchestrator Node

Edit `orchestrator/graph.py`:

```python
async def structuring_node(state: AgentState) -> Dict[str, Any]:
    """
    NEW ARCHITECTURE: Runs FIRST on raw transcript
    Performs semantic NLP analysis to identify conversation phases
    """
    content = state["file_path"].read_text(encoding='utf-8')

    # ENABLE SEMANTIC NLP ANALYSIS
    result = await structuring_agent.run(
        raw_transcript=content,
        use_semantic_nlp=True  # ← SET TO TRUE
    )

    # Extract components from semantic analysis
    if isinstance(result, dict):
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

### Option 2: Environment Variable

Add to `.env`:
```bash
USE_SEMANTIC_NLP=true
```

Update `config/settings.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...
    USE_SEMANTIC_NLP: bool = False
```

Update orchestrator node:
```python
result = await structuring_agent.run(
    raw_transcript=content,
    use_semantic_nlp=settings.USE_SEMANTIC_NLP
)
```

---

## Performance Considerations

### Standard Mode (Current)
- **Single LLM call**: Phase identification only
- **Execution time**: ~10-30 seconds (Mistral 7B)
- **Metadata**: Basic (phase, timestamp)

### Semantic NLP Mode (Enhanced)
- **Single LLM call**: Comprehensive analysis (same call, richer prompt)
- **Execution time**: ~30-60 seconds (Mistral 7B) - slightly longer due to complex JSON
- **Metadata**: Rich (intent, sentiment, entities, topics, discourse markers)

**Trade-off**: Slightly longer processing time for MUCH richer metadata that:
1. Improves chunk retrieval accuracy
2. Reduces KnowledgeAnalyst LLM calls (better filters = fewer chunks needed)
3. Enables advanced features (sentiment tracking, objection detection, engagement scoring)

**Net Result**: Overall pipeline may be FASTER due to more efficient retrieval.

---

## Current Status

- ✅ Semantic NLP analysis implemented in StructuringAgent
- ✅ AgentState updated with semantic fields
- ⏳ **TODO**: Update orchestrator to enable semantic NLP mode
- ⏳ **TODO**: Update ParserAgent to enrich turns with semantic metadata
- ⏳ **TODO**: Update ChunkerAgent to include semantic metadata in chunks
- ⏳ **TODO**: Update EmbedderAgent to store semantic metadata in Qdrant
- ⏳ **TODO**: Update KnowledgeAnalystAgent with semantic filtering strategies

---

## Testing Semantic NLP

Create test script:

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from agents.structuring.structuring_agent import StructuringAgent
from config.settings import settings

async def test_semantic_nlp():
    agent = StructuringAgent(settings)

    transcript_path = Path("data/transcripts/test_sprint01.txt")
    raw_text = transcript_path.read_text()

    # Test semantic NLP analysis
    result = await agent.run(
        raw_transcript=raw_text,
        use_semantic_nlp=True
    )

    print("Semantic NLP Analysis Results:")
    print(f"Phases: {len(result['conversation_phases'])}")
    print(f"Turns analyzed: {len(result['semantic_turns'])}")
    print(f"Entity types: {list(result['key_entities'].keys())}")
    print(f"Overall structure: {result['overall_structure']}")

if __name__ == "__main__":
    asyncio.run(test_semantic_nlp())
```

Run:
```bash
./venv/bin/python scripts/test_semantic_nlp.py
```

---

## Summary

**Where NLP Analysis Happens**: `StructuringAgent._construct_semantic_nlp_prompt()` + LLM call

**What It Extracts**:
1. Conversation phases with topics/sentiment
2. Per-turn intent/sentiment/discourse markers
3. Named entities (money, dates, locations, products)
4. Overall conversation structure metrics

**How It Enriches Pipeline**:
1. **StructuringAgent** → Rich semantic metadata
2. **ParserAgent** → Enriches dialogue turns with intent/sentiment
3. **ChunkerAgent** → Creates metadata-rich chunks
4. **EmbedderAgent** → Stores semantic metadata in Qdrant
5. **KnowledgeAnalystAgent** → Targeted retrieval with semantic filters

**Result**: Highly contextually aware pipeline with better accuracy and efficiency.
