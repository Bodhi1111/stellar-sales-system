# Stellar Sales System - Agentic Pipeline Architecture

## Current Pipeline Flow (Ingestion Workflow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION PIPELINE (Sprint 01)                       │
│                     Entry Point: file_path (transcript.txt)                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: SEQUENTIAL PROCESSING                        │
│                              (Fast - <5 seconds)                             │
└─────────────────────────────────────────────────────────────────────────────┘

    📄 Transcript File (75KB)
           ↓
    ┌──────────────┐
    │  1. PARSER   │  ← Extract transcript_id from header
    │   (Fast)     │  ← Parse dialogue turns with timestamps
    └──────┬───────┘  ← Extract speakers
           ↓
    ┌──────────────┐
    │2. STRUCTURING│  ← Identify conversation phases (LLM)
    │   (LLM)      │  ← "Opening", "Discovery", "Close", etc.
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │  3. CHUNKER  │  ← Split into 4500-char chunks (~5 chunks)
    │   (Fast)     │  ← 10% overlap for context preservation
    └──────┬───────┘
           ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 2: INTELLIGENCE CORE (PARALLEL EXECUTION)                 │
│                   ⚠️ BOTTLENECK: 2-3 minutes (80% of time)                   │
└─────────────────────────────────────────────────────────────────────────────┘

           ┌─────────────────────────┬─────────────────────────┐
           ↓                         ↓                         ↓
    ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
    │4a.KNOWLEDGE │          │4b. EMBEDDER │          │             │
    │  ANALYST    │          │             │          │ (Parallel   │
    │  ⚠️ SLOW    │          │  (Fast)     │          │  but Ollama │
    │             │          │             │          │  queues)    │
    │ Map Phase:  │          │ • Batch     │          │             │
    │ • 5 chunks  │          │   encode    │          │             │
    │ × 30s each  │          │ • Generate  │          │             │
    │ = 2.5 min   │          │   vectors   │          │             │
    │             │          │ • Store in  │          │             │
    │ Reduce:     │          │   Qdrant    │          │             │
    │ • 10s       │          │             │          │             │
    │             │          │ w/metadata: │          │             │
    │ Output:     │          │ - client    │          │             │
    │ • Entities  │          │ - date      │          │             │
    │ • Facts     │          │ - phase     │          │             │
    │ • Store Neo4j│         │             │          │             │
    └──────┬──────┘          └─────────────┘          └─────────────┘
           ↓
           ↓ (extracted_data available)
           ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│              PHASE 3: LEGACY DOWNSTREAM AGENTS (PARALLEL)                    │
│                          (30-45 seconds total)                               │
└─────────────────────────────────────────────────────────────────────────────┘

           ┌──────────────┬──────────────┬──────────────┐
           ↓              ↓              ↓              ↓
    ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
    │5a. EMAIL  │  │5b. SOCIAL │  │5c. SALES  │  │           │
    │   AGENT   │  │   AGENT   │  │   COACH   │  │  (Parallel│
    │  (LLM)    │  │  (LLM)    │  │   (LLM)   │  │   but     │
    │           │  │           │  │           │  │   queued) │
    │ Draft     │  │ Generate  │  │ Provide   │  │           │
    │ follow-up │  │ social    │  │ coaching  │  │           │
    │ email     │  │ posts     │  │ feedback  │  │           │
    └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────────┘
          └──────────┬────────────┬──────┘
                     ↓            ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: CRM AGGREGATION (LLM)                            │
│                            (10-15 seconds)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │  6. CRM     │
                    │   AGENT     │  ← Consolidate all insights
                    │  (LLM)      │  ← Format for Baserow
                    └──────┬──────┘  ← Add client_name to all tables
                           ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 5: PERSISTENCE (DATABASE WRITES)                       │
│                            (5-10 seconds)                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │7.PERSISTENCE│
                    │   AGENT     │
                    └──────┬──────┘
                           ↓
            ┌──────────────┼──────────────┬──────────────┐
            ↓              ↓              ↓              ↓
      ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
      │PostgreSQL│   │  Qdrant  │   │  Neo4j   │   │ Baserow  │
      │  (Main)  │   │ (Vectors)│   │  (Graph) │   │  (CRM)   │
      └──────────┘   └──────────┘   └──────────┘   └──────────┘
      • Structured  • Embeddings  • Entities    • 5 Tables:
      • Full record • Metadata    • Relations     - Clients
      • Upsert by   • Searchable  • Knowledge     - Meetings
        external_id                 graph         - Deals
                                                  - Comms
                                                  - Coaching

═══════════════════════════════════════════════════════════════════════════════

## Performance Metrics (75KB Real Transcript)

### BEFORE OPTIMIZATION (500 char chunks):
```
Total Time: 5+ minutes (TIMEOUT)
├─ Parser/Structuring/Chunker: 5s
├─ Knowledge Analyst: 4+ minutes ⚠️ (30 chunks × 8s)
├─ Embedder: 5s
├─ Email/Social/Coach: 45s
├─ CRM: 15s
└─ Persistence: 10s
```

### AFTER OPTIMIZATION v1 (2000 char chunks):
```
Total Time: ~3 minutes
├─ Parser/Structuring/Chunker: 5s
├─ Knowledge Analyst: 2 minutes (10 chunks × 12s)
├─ Embedder: 5s (with batching)
├─ Email/Social/Coach: 45s
├─ CRM: 15s
└─ Persistence: 10s
```

### AFTER OPTIMIZATION v2 (4500 char chunks):
```
Total Time: ~2.5 minutes (TARGET)
├─ Parser/Structuring/Chunker: 5s
├─ Knowledge Analyst: 2.5 minutes (5 chunks × 30s)
├─ Embedder: 5s (with batching)
├─ Email/Social/Coach: 45s
├─ CRM: 15s
└─ Persistence: 10s
```

═══════════════════════════════════════════════════════════════════════════════

## Identified Bottlenecks & Solutions

### 🚨 PRIMARY BOTTLENECK: Knowledge Analyst Agent
**Problem**: Sequential LLM calls for each chunk
**Root Cause**: Ollama serves requests sequentially (single-threaded)
**Impact**: 80% of total pipeline time

**Implemented Solutions**:
✅ Increased chunk size: 500 → 4500 chars (9x reduction in chunks)
✅ Added parallel processing (async gather)
✅ Added batching to embeddings

**Remaining Limitation**: Ollama queue processes sequentially

**Future Options**:
- Option B: Multiple Ollama instances (2-3 servers on different ports)
- Option C: Consolidate agents (single LLM call for all extraction)
- Option D: Switch to batched inference (vLLM, TGI)

═══════════════════════════════════════════════════════════════════════════════

## Key Architecture Patterns

### 1. Intelligence-First Design
```
Parse → Chunk → [Build Graph + Embed] → [Generate Outputs] → Persist
                      ↑                         ↑
                  Core Intel              Derived Content
```

### 2. Parallel Execution Points
- Knowledge Analyst || Embedder (both process chunks)
- Email || Social || Sales Coach (all use extracted_data)
- Final join before Persistence (ensures all data ready)

### 3. External ID Linking
- `transcript_id` extracted from file header
- Used as `external_id` across all systems
- Enables upsert logic (CREATE or UPDATE)
- Links all 5 Baserow tables

### 4. Metadata Enhancement (NEW)
- Embeddings now include:
  - `client_name` (for client-specific searches)
  - `meeting_date` (for temporal filtering)
  - `conversation_phase` (for phase-specific retrieval)
- Enables pre-filtering before vector search in RAG queries

═══════════════════════════════════════════════════════════════════════════════

## Data Flow Through State

```python
AgentState (TypedDict):
├─ file_path: Path                    # Input
├─ transcript_id: str                 # From parser
├─ structured_dialogue: List[Dict]    # From parser
├─ conversation_phases: List[Dict]    # From structuring
├─ chunks: List[str]                  # From chunker
├─ extracted_data: Dict               # From knowledge analyst (Neo4j)
├─ email_draft: str                   # From email agent
├─ social_content: Dict               # From social agent
├─ coaching_feedback: str             # From sales coach
├─ crm_data: Dict                     # From CRM agent (aggregated)
└─ db_save_status: Dict               # From persistence
```

═══════════════════════════════════════════════════════════════════════════════

## Recent Optimizations Applied

### Chunking Strategy
```python
# Before: 500 chars → 30 chunks for 75KB file
# After:  4500 chars → 5 chunks for 75KB file
RecursiveCharacterTextSplitter(
    chunk_size=4500,     # 9x increase
    chunk_overlap=450    # 10% overlap for context
)
```

### Parallel Processing
```python
# Before: Sequential loop
for chunk in chunks:
    result = llm.generate(chunk)

# After: Parallel async
tasks = [process_chunk(c) for c in chunks]
results = await asyncio.gather(*tasks)
```

### Embedding Batching
```python
# Before: Default batch
embeddings = model.encode(chunks)

# After: Explicit batching
embeddings = model.encode(chunks, batch_size=32)
```

### Metadata Enhancement
```python
# Before: Basic metadata
payload = {"transcript_id": id, "text": chunk}

# After: Rich metadata
payload = {
    "transcript_id": id,
    "text": chunk,
    "client_name": name,      # NEW
    "meeting_date": date,      # NEW
    "conversation_phase": phase # NEW
}
```

═══════════════════════════════════════════════════════════════════════════════
