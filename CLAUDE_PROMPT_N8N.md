# 📋 Claude Code Prompt for N8N RAG Workflow Implementation

Copy and paste this entire prompt to Claude Code in Cursor when working on the N8N workflow.

---

## CONTEXT: Critical Constraint Discovered

**Problem:** My sales call transcripts are 70 minutes long (~77KB, ~19,250 tokens) but Mistral 7B only handles 8,192 tokens. The transcript is **2.4x larger** than the model can process in a single call.

**Solution:** We MUST use RAG-enhanced extraction with semantic chunking. This isn't optional—it's required for long transcripts.

---

## PROJECT DETAILS

**Repository:** stellar-sales-system  
**Branch:** n8n-rag-workflow  
**N8N:** Running locally via Docker at http://localhost:5678/  
**Folder to Watch:** `/Users/joshuavaughan/Documents/McAdams Transcripts` (Google Drive sync'd)

---

## WHAT WE'RE BUILDING

A complete N8N workflow that:

### 1. File Monitoring
- Watches McAdams Transcripts folder for new `.txt` files
- Triggers automatically when transcript appears

### 2. Transcript Processing
- **Parse:** Extract header metadata + structured dialogue turns
- **Chunk:** Create parent-child hierarchy (header + parents + children)
- **Embed:** Generate 768-dim vectors using BAAI/bge-base-en-v1.5
- **Store:** Save to Qdrant vector database

### 3. RAG-Enhanced CRM Extraction
Since transcripts exceed token limits, we use **multi-query RAG**:

**Query 1 - Client Info** (top 5 chunks):
- Search: "client name, email, marital status, children, estate value"
- Extract: Client demographic data

**Query 2 - Meeting Details** (top 5 chunks):
- Search: "meeting date, time, duration, agenda"
- Extract: Meeting metadata

**Query 3 - Deal Information** (top 10 chunks):
- Search: "pricing, products discussed, deal amount, deposit, objections"
- Extract: Sales pipeline data

**Query 4 - Communications** (top 5 chunks):
- Search: "action items, next steps, follow-up"
- Extract: Follow-up email draft, social content

**Query 5 - Sales Coaching** (top 10 chunks):
- Search: "objections, missed opportunities, coaching feedback"
- Extract: Improvement insights

Each query:
1. Searches Qdrant for relevant chunks
2. Feeds focused context to Mistral 7B (under token limit)
3. Extracts specific CRM fields
4. Aggregates into complete CRM record

### 4. Baserow Sync
- **5 CRM tables** (parallel): Clients, Meetings, Deals, Communications, Coaching
- **1 Chunks table** (loop): All chunks with semantic metadata

---

## ENVIRONMENT VARIABLES

Use existing `.env` from stellar-sales-system:

```bash
# LLM
OLLAMA_API_URL=http://host.docker.internal:11434/api/generate
LLM_MODEL_NAME=mistral:7b

# Vector Database
QDRANT_URL=http://host.docker.internal:6333

# Embeddings
EMBEDDING_MODEL_NAME=BAAI/bge-base-en-v1.5

# Baserow CRM
BASEROW_URL=https://api.baserow.io
BASEROW_TOKEN=<from .env>
BASEROW_CLIENTS_ID=704
BASEROW_MEETINGS_ID=705
BASEROW_DEALS_ID=706
BASEROW_COMMUNICATIONS_ID=707
BASEROW_SALES_COACHING_ID=708
BASEROW_CHUNKS_ID=709

# PostgreSQL (if needed)
POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT
```

**Docker N8N Start Command:**
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

---

## EXISTING CODE TO REFERENCE

### Parser Logic (`agents/parser/parser_agent.py`)

**Header Extraction (lines 88-220):**
Three patterns to handle:
- **Pattern A:** Line 1=title, 2=name, 4=email, 6=date, 8=id, 10=url, 12=duration
- **Pattern B:** Line 1=title, 3=name, 5=email, 7=date, 9=id, 11=url, 13=duration  
- **Pattern C:** Line 1=title, 4=url, 7=date, 10=duration, 13=name, 16=email

**Dialogue Regex (lines 16-19):**
```python
bracketed_pattern = r'\[(.*?)\]\s+([^:]+):\s+(.*)'  # [00:15:32] Speaker Name: Text...
dashed_pattern = r'^\s*(\d{2}:\d{2}:\d{2})\s+-\s+(.+)$'  # 00:15:32 - Speaker Name
```

### Chunking Logic (`agents/chunker/chunker.py`)

**Parameters (lines 20-24):**
```python
turns_per_parent=7
min_turns_per_parent=5
max_turns_per_parent=10
```

**Output (lines 102-107):**
```python
{
  "all_chunks": [...],      # For Baserow (header + parents + children)
  "child_chunks": [...],    # For embedding (speaker turns only)
  "parent_chunks": [...],   # For Qdrant payload (context)
  "header_chunk": {...}     # For metadata
}
```

### Semantic Chunker (`core/semantic_chunker.py`)
Full parent-child hierarchy implementation with UUIDs

### Embedder (`agents/embedder/embedder_agent.py`)
- Model: BAAI/bge-base-en-v1.5 (768 dimensions)
- Embed ONLY child chunks (speaker turns)

### Qdrant Storage (`core/qdrant_rag_mixin.py`)
- Collection: "transcripts"
- Lines 79-137: Hybrid search (BM25 + Vector + RRF)
- Child chunks: with vectors
- Parent chunks: payload only (context)

### Baserow Sync (`core/database/baserow.py`)

**Chunk Metadata (lines 632-696):**
- chunk_id (UUID), parent_id, chunk_type
- external_id, transcript_filename
- text, speaker_name, timestamps
- conversation_phase, sales_stage
- detected_topics (JSON array)
- intent, sentiment, discourse_marker
- contains_entity, turn_count, speaker_balance

**Valid Select Field Values (lines 649-656):**
```python
VALID_SALES_STAGES = {"Setting up for meeting", "Assistant Intro Rep", "Greeting", 
                      "Client Motivation", "Set Meeting Agenda", "Establish Credibility",
                      "Discovery", "Compare Options", "Present Solution", "Pricing",
                      "Objection Handling", "Closing", "Unknown"}
VALID_INTENTS = {"question", "statement", "objection", "agreement", "proposal", "clarification"}
VALID_SENTIMENTS = {"positive", "neutral", "concerned", "excited"}  # Note: No "negative"
VALID_DISCOURSE_MARKERS = {"transition", "confirmation", "hedge", "emphasis", "none"}
```

**Email Handling (lines 282-293):**
- If multiple emails, take first one
- Validate format before syncing

---

## N8N WORKFLOW STRUCTURE

```
Node 1: File Watcher (LocalFileTrigger)
  ↓
Node 2: Read Text File
  ↓
Node 3: Parse Transcript (Code - JavaScript)
  - Extract header metadata
  - Parse dialogue turns with regex
  - Output: {header_metadata, structured_dialogue}
  ↓
Node 4: Semantic Chunking (Code - JavaScript)
  - Create parent-child hierarchy
  - Generate UUIDs
  - Output: {all_chunks, child_chunks, parent_chunks, header_chunk}
  ↓
Node 5: Generate Embeddings (HTTP Request)
  - POST to sentence-transformers API
  - Model: BAAI/bge-base-en-v1.5
  - Input: child_chunks texts only
  - Output: 768-dim vectors
  ↓
Node 6: Store in Qdrant (HTTP Request)
  - POST /collections/transcripts/points/upsert
  - Child chunks: with vectors
  - Parent chunks: payload only
  ↓
Node 7-11: RAG-Enhanced Extraction (Loop)
  For each CRM category:
    → Query Qdrant (HTTP Request)
    → Extract with Ollama (Ollama Chat Model)
    → Aggregate results
  ↓
Node 12-16: Sync to 5 CRM Tables (Parallel HTTP Requests)
  - Clients, Meetings, Deals, Communications, Coaching
  ↓
Node 17: Sync Chunks Table (Loop)
  - Iterate all_chunks
  - Validate semantic metadata
  - POST to Baserow Chunks table
  ↓
Node 18: Success Response
```

---

## IMPLEMENTATION TASKS

### Task 1: Create Workflow JSON Structure
File: `n8n-workflow-rag.json`

Define all nodes with proper connections using n8n node types:
- LocalFileTrigger (file watcher)
- ReadBinaryFile
- Code (JavaScript)
- HTTP Request
- Ollama Chat Model
- Loop Over Items
- Set (data transformation)

### Task 2: JavaScript - Parse Transcript

Implement in Code node:

```javascript
// Extract header metadata (3 patterns)
function extractHeader(lines) {
  // Pattern detection logic
  // Return: {transcript_id, meeting_title, client_name, email, date, duration, url}
}

// Parse dialogue turns
function parseDialogue(content) {
  const bracketedPattern = /\[(.*?)\]\s+([^:]+):\s+(.*)/;
  const dashedPattern = /^\s*(\d{2}:\d{2}:\d{2})\s+-\s+(.+)$/;
  
  // Extract turns: [{timestamp, speaker_name, text}, ...]
}

// Main execution
const content = $input.item.json.data;
const lines = content.split('\n');
const header = extractHeader(lines);
const dialogue = parseDialogue(content);

return {
  json: {
    header_metadata: header,
    structured_dialogue: dialogue
  }
};
```

### Task 3: JavaScript - Semantic Chunking

```javascript
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function createChunks(header, dialogue, transcriptId) {
  const turns_per_parent = 7;
  const min_turns = 5;
  const max_turns = 10;
  
  // Header chunk
  const headerChunk = {
    chunk_id: generateUUID(),
    parent_id: null,
    chunk_type: "header",
    external_id: transcriptId,
    text: header.raw_text,
    // ... metadata fields
  };
  
  // Create parent chunks (5-10 turn segments)
  const parentChunks = [];
  const childChunks = [];
  
  let currentParentId = generateUUID();
  let turnCount = 0;
  let currentTurns = [];
  
  for (const turn of dialogue) {
    // Create child chunk for this turn
    const childChunk = {
      chunk_id: generateUUID(),
      parent_id: currentParentId,
      chunk_type: "child",
      external_id: transcriptId,
      text: turn.text,
      speaker_name: turn.speaker_name,
      timestamp: turn.timestamp,
      // ... more metadata
    };
    childChunks.push(childChunk);
    currentTurns.push(turn);
    turnCount++;
    
    // Create parent chunk when threshold reached
    if (turnCount >= turns_per_parent) {
      const parentChunk = {
        chunk_id: currentParentId,
        parent_id: null,
        chunk_type: "parent",
        external_id: transcriptId,
        text: currentTurns.map(t => t.text).join('\n'),
        turn_count: turnCount,
        // ... metadata
      };
      parentChunks.push(parentChunk);
      
      // Reset for next parent
      currentParentId = generateUUID();
      turnCount = 0;
      currentTurns = [];
    }
  }
  
  // Handle remaining turns
  if (currentTurns.length > 0) {
    const parentChunk = {
      chunk_id: currentParentId,
      parent_id: null,
      chunk_type: "parent",
      external_id: transcriptId,
      text: currentTurns.map(t => t.text).join('\n'),
      turn_count: currentTurns.length
    };
    parentChunks.push(parentChunk);
  }
  
  return {
    all_chunks: [headerChunk, ...parentChunks, ...childChunks],
    child_chunks: childChunks,
    parent_chunks: parentChunks,
    header_chunk: headerChunk
  };
}

// Execute
const input = $input.item.json;
const chunks = createChunks(
  input.header_metadata,
  input.structured_dialogue,
  input.header_metadata.transcript_id
);

return { json: chunks };
```

### Task 4: RAG-Enhanced Extraction Loop

**Critical Implementation:**

Use Loop node to iterate over CRM categories:

```javascript
// Define extraction queries
const categories = [
  {
    name: "client_info",
    query: "client name email marital status children estate value",
    top_k: 5,
    fields: ["client_name", "client_email", "marital_status", "children_count", "estate_value"]
  },
  {
    name: "meeting_details",
    query: "meeting date time duration agenda",
    top_k: 5,
    fields: ["meeting_date", "meeting_time", "duration_minutes", "meeting_title"]
  },
  {
    name: "deal_info",
    query: "pricing products deal amount deposit objections win probability",
    top_k: 10,
    fields: ["product_discussed", "deal", "deposit", "objections_raised", "win_probability"]
  },
  {
    name: "communications",
    query: "action items next steps follow-up email",
    top_k: 5,
    fields: ["action_items", "follow_up_email_draft", "social_media_quote"]
  },
  {
    name: "coaching",
    query: "objections missed opportunities coaching feedback improvement",
    top_k: 10,
    fields: ["coaching_opportunities"]
  }
];
```

For each category:
1. **Query Qdrant:** POST to `/collections/transcripts/points/search` with query vector
2. **Extract Focused Context:** Feed top_k chunks to Ollama
3. **Parse Response:** Extract specific fields
4. **Aggregate:** Merge into final CRM object

### Task 5: Baserow Sync Nodes

**CRM Tables (5 parallel HTTP Requests):**

Each node:
- Method: POST
- URL: `{{ $env.BASEROW_URL }}/api/database/rows/table/{{ $env.BASEROW_TABLE_ID }}/`
- Headers: `Authorization: Token {{ $env.BASEROW_TOKEN }}`
- Body: Transform CRM data to Baserow fields

**Chunks Table (Loop node):**

```javascript
// Validate and transform each chunk
for (const chunk of allChunks) {
  // Validate sales_stage
  if (chunk.sales_stage && !VALID_SALES_STAGES.includes(chunk.sales_stage)) {
    chunk.sales_stage = "Unknown";
  }
  
  // Map negative sentiment
  if (chunk.sentiment === "negative") {
    chunk.sentiment = "concerned";
  }
  
  // Convert topics to JSON string
  if (Array.isArray(chunk.detected_topics)) {
    chunk.detected_topics = JSON.stringify(chunk.detected_topics);
  }
  
  // POST to Baserow
  await post(`${baserowUrl}/api/database/rows/table/709/`, chunk);
}
```

---

## CRITICAL QUESTIONS TO ADDRESS

1. **Sentence-Transformers API:** How are we hosting BAAI/bge-base-en-v1.5 locally? Via HuggingFace API, local server, or n8n integration?

2. **Qdrant Schema:** What's the exact point structure for child vs parent chunks?

3. **RAG Aggregation:** How do we merge 5 separate LLM responses into one CRM object?

4. **Error Handling:** What happens if a transcript fails mid-processing?

5. **Testing:** Do you have a 70-minute test transcript ready?

---

## SUCCESS CRITERIA

✅ File watcher triggers on new transcripts in McAdams folder  
✅ 70-minute transcripts process without token limit errors  
✅ Parent-child chunks created (~30 children, ~4-6 parents per 70-min)  
✅ Child chunks embedded with 768-dim vectors  
✅ Qdrant stores chunks with proper metadata  
✅ RAG queries return relevant chunks (not full transcript)  
✅ Mistral 7B extracts CRM data from focused chunks (under 8k tokens)  
✅ All 6 Baserow tables populated accurately  
✅ Chunks table has semantic metadata (sales_stage, intent, sentiment)  
✅ No truncation or data loss  
✅ Total time: 90-120 seconds per 70-min transcript  
✅ Visual debugging shows clear flow through all nodes  

---

## LET'S START

I'm ready to:
1. Review the workflow architecture
2. Create the n8n-workflow-rag.json file
3. Implement JavaScript Code nodes
4. Test with real 70-minute transcripts
5. Debug and iterate

**What should we tackle first?**
- Workflow structure and node layout?
- Parse Transcript JavaScript implementation?
- Semantic Chunking JavaScript implementation?
- RAG extraction loop logic?

Your call!

