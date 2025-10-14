# N8N RAG-Powered CRM Workflow

Build a complete N8N workflow that monitors the McAdams Transcripts folder, performs semantic analysis with parent-child chunking, generates embeddings for Qdrant RAG, and syncs to all 6 Baserow tables.

## Architecture Overview

```
File Watcher → Read Text → Parse → Chunk (Parent-Child) → Embed → Qdrant Store
                                                                        ↓
                                                            RAG-Enhanced CRM Extraction
                                                        (Query Qdrant for relevant chunks,
                                                         Process with LLM in focused batches)
                                                                        ↓
                        ┌──────────────────────────────────────────────┴────────────────┐
                        ↓                                                                ↓
            Sync to 5 CRM Tables                                            Sync Chunks Table
    (Clients, Meetings, Deals, Comms, Coaching)                        (with semantic metadata)
```

**Why RAG is Required:**
- 70-minute transcripts = ~19,250 tokens
- Mistral 7B context limit = 8,192 tokens
- Transcript is 2.4x larger than model can handle
- RAG breaks transcript into processable chunks, queries relevant context per CRM field

## Key Components to Build

### 1. File Watcher Configuration
- Monitor folder: `/Users/joshuavaughan/Documents/McAdams Transcripts`
- Trigger on new `.txt` files only
- Pass file path to next node

### 2. Transcript Processing Chain

**Node: Read Transcript**
- Read file contents from watcher path
- Extract header metadata using patterns from `parser_agent.py:88-220`
- Parse transcript_id, meeting_title, date, client_name, email, duration

**Node: Parse Structured Dialogue**
- Apply regex patterns from `parser_agent.py:16-19`:
  - Bracketed: `[00:15:32] Speaker Name: Text...`
  - Dashed: `00:15:32 - Speaker Name`
- Extract: timestamp, speaker_name, text for each turn
- Assign conversation_phase to each turn

**Node: Semantic Chunking (Parent-Child)**
- Implement logic from `chunker.py:26-107`
- Create three chunk types:
  1. Header chunk (metadata, no embedding)
  2. Parent chunks (5-10 turn segments, context only)
  3. Child chunks (individual turns, embedded)
- Each chunk needs UUID, parent_id, metadata fields

### 3. Embedding & RAG Storage

**Node: Generate Embeddings**
- Model: BAAI/bge-base-en-v1.5 (768-dimensional vectors)
- Embed ONLY child chunks (speaker turns)
- Output: vectors + metadata

**Node: Store in Qdrant**
- Collection: "transcripts"
- Store child chunks with vectors
- Store parent chunks in payload (no vectors)
- Include metadata: conversation_phase, speaker_name, timestamp, sales_stage

### 4. RAG-Enhanced CRM Data Extraction

**Multi-Query RAG Strategy:**

Since 70-minute transcripts exceed Mistral 7B's 8,192 token limit, we use RAG to query relevant chunks for each CRM category:

1. **Client Info Extraction:**
   - Query: "client name, email, marital status, children, estate value"
   - Qdrant search → top 5 relevant chunks
   - Feed to Mistral: "Extract client info from: {chunks}"

2. **Meeting Details:**
   - Query: "meeting date, time, duration, agenda"
   - Qdrant → top 5 chunks
   - Extract meeting metadata

3. **Deal Information:**
   - Query: "pricing, products discussed, deal amount, deposit, objections"
   - Qdrant → top 10 chunks
   - Extract deal fields

4. **Follow-up & Communications:**
   - Query: "action items, next steps, follow-up"
   - Qdrant → top 5 chunks
   - Generate email draft

5. **Sales Coaching:**
   - Query: "objections, missed opportunities, coaching feedback"
   - Qdrant → top 10 chunks
   - Extract coaching insights

**Ollama Chat Model Node:**
- Use n8n's native Ollama Chat Model node
- Model: mistral:7b
- System prompt: "You are a sales CRM data extraction expert"
- Response format: JSON
- Timeout: 180 seconds per extraction

### 5. Baserow Sync (6 Tables)

**Parallel Nodes (Tables 1-5):**
- Clients (table 704)
- Meetings (table 705)
- Deals (table 706)
- Communications (table 707)
- Sales Coaching (table 708)

**Loop Node (Table 6):**
- Chunks table (table 709)
- Loop through all_chunks array
- For each chunk, POST to Baserow with:
  - chunk_id, parent_id, chunk_type, external_id
  - text, speaker_name, timestamps
  - conversation_phase, sales_stage
  - detected_topics (JSON array)
  - intent, sentiment, discourse_marker
  - contains_entity, turn_count, speaker_balance
- Validate single_select fields against allowed values

## Implementation Steps

### Step 1: Create N8N Workflow JSON Structure
- File: `n8n-workflow-rag.json`
- Use n8n node types:
  - LocalFileTrigger (file watcher)
  - ReadBinaryFile
  - Code (JavaScript for parsing/chunking)
  - HTTP Request (Embedding API, Qdrant, Baserow)
  - Ollama Chat Model (for RAG extraction)
  - Loop Over Items (for chunks sync)

### Step 2: Code Node: Parse Transcript
- JavaScript function replicating `parser_agent.py` logic
- Extract header metadata (3 patterns)
- Parse dialogue turns with regex (2 patterns)
- Return structured_dialogue array

### Step 3: Code Node: Semantic Chunking
- JavaScript implementing `semantic_chunker.py` logic
- Create parent-child hierarchy
- Generate UUIDs for chunk_id and parent_id
- Output: {all_chunks, child_chunks, parent_chunks, header_chunk}

### Step 4: HTTP Request Nodes

**Embedding Generation:**
- POST to sentence-transformers API
- Model: BAAI/bge-base-en-v1.5
- Body: {texts: [child_chunk_texts]}
- Returns: 768-dim vectors

**Qdrant Storage:**
- POST to Qdrant upsert endpoint
- Collection: transcripts
- Child chunks: with vectors
- Parent chunks: payload only

**Baserow Syncs:**
- 6 HTTP Request nodes (5 parallel + 1 in loop)
- Authorization: `Token $env.BASEROW_TOKEN`
- Transform field names to field IDs

### Step 5: RAG-Enhanced Extraction Loop
- Loop node for each CRM category (5 iterations)
- For each iteration:
  1. Query Qdrant with category-specific search
  2. Feed relevant chunks to Ollama Chat Model
  3. Extract category fields
  4. Aggregate into final CRM object

### Step 6: Error Handling
- Add Error Trigger workflow
- Catch and log failures
- Optional: notifications on error

### Step 7: Environment Variables

Use existing `.env` from stellar-sales-system:

**LLM Configuration:**
- OLLAMA_API_URL=http://host.docker.internal:11434/api/generate
- LLM_MODEL_NAME=mistral:7b

**Vector Database:**
- QDRANT_URL (local Qdrant instance)

**Embedding Model:**
- EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5

**Baserow CRM:**
- BASEROW_URL, BASEROW_TOKEN
- BASEROW_CLIENTS_ID (704)
- BASEROW_MEETINGS_ID (705)
- BASEROW_DEALS_ID (706)
- BASEROW_COMMUNICATIONS_ID (707)
- BASEROW_SALES_COACHING_ID (708)
- BASEROW_CHUNKS_ID (709)

**N8N Docker Configuration:**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -v /Users/joshuavaughan/Documents/McAdams\ Transcripts:/data/transcripts:ro \
  --env-file /Users/joshuavaughan/dev/Projects/stellar-sales-system/.env \
  -e OLLAMA_API_URL=http://host.docker.internal:11434/api/generate \
  -e QDRANT_URL=http://host.docker.internal:6333 \
  docker.n8n.io/n8nio/n8n
```

## Key Implementation Details

### Chunk Metadata Fields
Each chunk must include:
- chunk_id (UUID), parent_id (UUID or empty), chunk_type (header/parent/child)
- external_id (transcript ID), transcript_filename
- text, speaker_name, start_time, end_time
- conversation_phase, timestamp_start, timestamp_end
- sales_stage, detected_topics (JSON array)
- intent, sentiment, discourse_marker
- contains_entity (boolean), turn_count (int), speaker_balance (float)

### File Watcher Path
- Path: `/Users/joshuavaughan/Documents/McAdams Transcripts`
- Pattern: `*.txt`
- Watch for: new files only

### Semantic Chunking Parameters
- turns_per_parent: 7
- min_turns_per_parent: 5
- max_turns_per_parent: 10

### Qdrant Storage Strategy
- Only child chunks get embeddings
- Parent chunks stored in payload for context
- Metadata filters: conversation_phase, sales_stage, speaker_name

## Testing Plan

1. Place test transcript in McAdams folder
2. Verify file watcher triggers
3. Check parsing output (structured_dialogue)
4. Verify chunking creates parent-child hierarchy
5. Confirm embeddings generated for child chunks only
6. Check Qdrant storage (vectors + metadata)
7. Verify RAG queries return relevant chunks
8. Confirm CRM extraction from RAG chunks (not full transcript)
9. Confirm all 6 Baserow tables populated
10. Validate semantic metadata in Chunks table

## Success Criteria

- File watcher detects new transcripts automatically
- 70-minute transcripts processed without token limit errors
- Parent-child chunks created with proper UUIDs and relationships
- Child chunks embedded and stored in Qdrant
- RAG queries retrieve relevant chunks for each CRM category
- CRM data extracted via multiple focused LLM calls (not truncated)
- All 6 Baserow tables synced with accurate data
- Chunks table populated with semantic metadata
- Total processing time: 90-120 seconds per 70-min transcript
- Visual debugging shows clear data flow through all nodes
- Errors caught and logged with useful context

## Files to Create

1. `n8n-workflow-rag.json` - Complete workflow definition
2. `N8N_RAG_SETUP_GUIDE.md` - Installation and configuration guide
3. `scripts/test-n8n-workflow.sh` - Test script for validation
4. `CLAUDE_PROMPT_N8N.md` - Detailed prompt for Claude Code assistance

## Implementation Tasks

- [ ] Create n8n-workflow-rag.json with all nodes
- [ ] Implement JavaScript parsing logic (Code node)
- [ ] Implement JavaScript semantic chunking (Code node)
- [ ] Configure embedding generation (HTTP Request)
- [ ] Configure Qdrant storage (HTTP Request)
- [ ] Implement RAG extraction loop (multiple Ollama + Qdrant queries)
- [ ] Configure 5 parallel Baserow CRM syncs
- [ ] Configure Loop node for Chunks table sync
- [ ] Add Error Trigger workflow
- [ ] Create N8N_RAG_SETUP_GUIDE.md
- [ ] Test with 70-minute transcript
- [ ] Verify no truncation, all data captured

