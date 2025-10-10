# Stellar Sales System - Pipeline Architecture Visual

## Current Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STELLAR SALES SYSTEM PIPELINE                        │
│                        (Intelligence First Architecture)                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAW TRANSCRIPT│    │   STRUCTURING   │    │     PARSER      │    │    CHUNKER      │
│                 │    │     AGENT       │    │     AGENT       │    │     AGENT       │
│ • Meeting Title │───▶│                 │───▶│                 │───▶│                 │
│ • Client Name   │    │ • Semantic NLP  │    │ • Header Meta   │    │ • Header Chunk  │
│ • Email         │    │ • Conversation  │    │ • Dialogue Parse│    │ • Dialogue Chks │
│ • Date/Time     │    │   Phases        │    │ • Dual Pattern  │    │ • Metadata Pres │
│ • Transcript ID │    │ • Entity Extract│    │   Detection     │    │                 │
│ • Meeting URL   │    │ • Sentiment     │    │                 │    │                 │
│ • Duration      │    │ • Intent        │    │                 │    │                 │
│ • Dialogue      │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │                       │
                                ▼                       ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │  SEMANTIC TURNS │    │  HEADER METADATA│    │  CHUNKS WITH    │
                       │  • Intent       │    │  • meeting_title│    │    METADATA     │
                       │  • Sentiment    │    │  • client_name  │    │  • chunk_type   │
                       │  • Discourse    │    │  • client_email │    │  • index        │
                       │  • Entities     │    │  • meeting_date │    │  • phase        │
                       │                 │    │  • meeting_time │    │  • speakers     │
                       │                 │    │  • transcript_id│    │  • intent       │
                       │                 │    │  • meeting_url  │    │  • sentiment    │
                       │                 │    │  • duration     │    │                 │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                              │
                                                                              ▼
                                                                    ┌─────────────────┐
                                                                    │   EMBEDDER      │
                                                                    │     AGENT       │
                                                                    │                 │
                                                                    │ • Vector Embed  │
                                                                    │ • Qdrant Store  │
                                                                    │ • Metadata      │
                                                                    │ • Filtering     │
                                                                    └─────────────────┘
                                                                              │
                                                                              ▼
                                                                    ┌─────────────────┐
                                                                    │     QDRANT      │
                                                                    │   VECTOR DB     │
                                                                    │                 │
                                                                    │ • 32 Chunks     │
                                                                    │ • Embeddings    │
                                                                    │ • Metadata      │
                                                                    │ • Filtering     │
                                                                    └─────────────────┘
                                                                              │
                                                                              ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │     EMAIL       │    │     SOCIAL      │    │  SALES COACH    │
                       │     AGENT       │    │     AGENT       │    │     AGENT       │
                       │                 │    │                 │    │                 │
                       │ • Follow-up     │    │ • Content Posts │    │ • Performance   │
                       │   Drafts        │    │ • Opportunities │    │   Feedback      │
                       │ • Templates     │    │ • Engagement    │    │ • Coaching      │
                       │                 │    │                 │    │   Tips          │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │                       │
                                ▼                       ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │  EMAIL DRAFTS   │    │  SOCIAL CONTENT │    │ COACHING FEEDBK │
                       │  • Templates    │    │  • Posts        │    │  • Performance  │
                       │  • Personalize  │    │  • Opportunities│    │  • Tips         │
                       │  • Follow-up    │    │  • Engagement   │    │  • Areas        │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │                       │
                                └───────────────────────┼───────────────────────┘
                                                        ▼
                                               ┌─────────────────┐
                                               │      CRM        │
                                               │     AGENT       │
                                               │                 │
                                               │ • Aggregate     │
                                               │ • Insights      │
                                               │ • Client Data   │
                                               │ • Meeting Info  │
                                               │ • Outcomes      │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   PERSISTENCE   │
                                               │     AGENT       │
                                               │                 │
                                               │ • PostgreSQL    │
                                               │ • Baserow Sync  │
                                               │ • Neo4j Graph   │
                                               │ • Data Storage  │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   DATA STORES   │
                                               │                 │
                                               │ • PostgreSQL    │
                                               │ • Baserow CRM   │
                                               │ • Neo4j Graph   │
                                               │ • Qdrant Vectors│
                                               └─────────────────┘
```

## Header Extraction Enhancement Details

### Dual Pattern Detection
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           HEADER EXTRACTION LOGIC                              │
└─────────────────────────────────────────────────────────────────────────────────┘

RAW TRANSCRIPT HEADER (First 14 lines):
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Line 1:  [MEETING TITLE]                                                       │
│ Line 2:  [CLIENT NAME] OR [BLANK] ← Pattern Detection Point                    │
│ Line 3:  [BLANK] OR [CLIENT NAME]                                              │
│ Line 4:  [BLANK] OR [CLIENT EMAIL]                                             │
│ Line 5:  [CLIENT EMAIL] OR [BLANK]                                             │
│ Line 6:  [BLANK] OR [MEETING DATE+TIME]                                        │
│ Line 7:  [MEETING DATE+TIME] OR [BLANK]                                        │
│ Line 8:  [BLANK] OR [TRANSCRIPT ID]                                            │
│ Line 9:  [TRANSCRIPT ID] OR [BLANK]                                            │
│ Line 10: [BLANK] OR [MEETING URL]                                              │
│ Line 11: [MEETING URL] OR [BLANK]                                              │
│ Line 12: [BLANK] OR [DURATION]                                                 │
│ Line 13: [DURATION] OR [BLANK]                                                 │
│ Line 14: [BLANK] OR [FIRST TIMESTAMP]                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

PATTERN DETECTION:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ if Line 2 has content:                                                         │
│   → PATTERN A (George Padron): No blank after title                           │
│   → client_name = Line 2, email = Line 4, date = Line 6, etc.                │
│                                                                                 │
│ if Line 2 is blank:                                                            │
│   → PATTERN B (Robin Michalek): Blank line after title                        │
│   → client_name = Line 3, email = Line 5, date = Line 7, etc.                │
└─────────────────────────────────────────────────────────────────────────────────┘

EXTRACTED METADATA:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ {                                                                              │
│   'meeting_title': 'Robin Michalek: Estate Planning Advisor Meeting',          │
│   'client_name': 'Robin Michalek',                                             │
│   'client_email': 'robincabo@msn.com',                                         │
│   'meeting_date': '2025-09-26',                                                │
│   'meeting_time': '20:00:00',                                                  │
│   'transcript_id': '60470637',                                                 │
│   'meeting_url': 'https://fathom.video/calls/422278831',                       │
│   'duration_minutes': 65.63155018333333                                        │
│ }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### 1. Ingestion Phase
```
RAW TRANSCRIPT → STRUCTURING → PARSER → CHUNKER → EMBEDDER
     │              │           │         │          │
     ▼              ▼           ▼         ▼          ▼
[Header+Body] → [NLP Analysis] → [Header Meta] → [Header Chunk] → [Vector Store]
```

### 2. Processing Phase
```
EMBEDDER → EMAIL AGENT → CRM AGENT → PERSISTENCE
    │         │            │           │
    ▼         ▼            ▼           ▼
[Vectors] → [Drafts] → [Insights] → [Storage]
    │         │            │           │
    ▼         ▼            ▼           ▼
[Qdrant] → [Templates] → [Client Data] → [PostgreSQL]
                           │           │
                           ▼           ▼
                      [Meeting Info] → [Baserow]
                           │           │
                           ▼           ▼
                      [Outcomes] → [Neo4j]
```

### 3. Knowledge Graph Integration
```
HEADER METADATA → KNOWLEDGE ANALYST → NEO4J GRAPH
      │                  │                │
      ▼                  ▼                ▼
[Client Info] → [Entity Extraction] → [Relationships]
      │                  │                │
      ▼                  ▼                ▼
[Meeting Data] → [Graph Building] → [Client Nodes]
      │                  │                │
      ▼                  ▼                ▼
[Transcript ID] → [Meeting Nodes] → [Product Nodes]
```

## Agent State Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT STATE                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

Initial State:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ {                                                                              │
│   "file_path": Path("transcript.txt"),                                         │
│   "raw_text": "meeting content...",                                           │
│   "transcript_id": null,                                                       │
│   "header_metadata": null,                                                     │
│   "chunks": null,                                                              │
│   "structured_dialogue": null,                                                 │
│   "conversation_phases": null,                                                 │
│   "semantic_turns": null,                                                      │
│   "extracted_entities": null,                                                  │
│   "crm_data": null,                                                            │
│   "email_draft": null,                                                         │
│   "social_content": null,                                                      │
│   "coaching_feedback": null,                                                   │
│   "db_save_status": null                                                       │
│ }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

After Structuring Agent:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ {                                                                              │
│   "conversation_phases": [{"phase": "client's estate details", ...}],          │
│   "semantic_turns": [{"timestamp": "00:00:59", "intent": "greeting", ...}],   │
│   "key_entities_nlp": {"PERSON": ["Robin Michalek"], ...},                    │
│   "conversation_structure": {"total_turns": 320, ...}                          │
│ }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

After Parser Agent:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ {                                                                              │
│   "transcript_id": "60470637",                                                 │
│   "header_metadata": {                                                         │
│     "meeting_title": "Robin Michalek: Estate Planning Advisor Meeting",        │
│     "client_name": "Robin Michalek",                                           │
│     "client_email": "robincabo@msn.com",                                       │
│     "meeting_date": "2025-09-26",                                              │
│     "meeting_time": "20:00:00",                                                │
│     "transcript_id": "60470637",                                               │
│     "meeting_url": "https://fathom.video/calls/422278831",                     │
│     "duration_minutes": 65.63155018333333                                      │
│   },                                                                            │
│   "structured_dialogue": [                                                     │
│     {"timestamp": "00:00:59", "speaker": "Gygy Cruz", "text": "Hi, this is...", "conversation_phase": "greeting", "intent": "greeting", "sentiment": "positive"}, │
│     ...                                                                        │
│   ]                                                                             │
│ }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘

After Chunker Agent:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ {                                                                              │
│   "chunks": [                                                                  │
│     {                                                                          │
│       "text": "Robin Michalek: Estate Planning Advisor Meeting\\n\\nRobin Michalek\\n\\nrobincabo@msn.com...", │
│       "chunk_type": "header",                                                  │
│       "index": 0,                                                              │
│       "conversation_phase": null,                                              │
│       "speakers": []                                                           │
│     },                                                                         │
│     {                                                                          │
│       "text": "[00:00:59] Gygy Cruz: Hi, this is Gigi from McAdams Group...", │
│       "chunk_type": "dialogue",                                                │
│       "index": 1,                                                              │
│       "conversation_phase": "greeting",                                        │
│       "speakers": ["Gygy Cruz"],                                               │
│       "dominant_intent": "greeting",                                           │
│       "dominant_sentiment": "positive",                                        │
│       "contains_entities": true,                                               │
│       "discourse_markers": ["greeting"]                                        │
│     },                                                                         │
│     ...                                                                        │
│   ]                                                                             │
│ }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Performance Optimizations

### 1. Header Extraction (NEW)
- **Before**: LLM extraction took 44+ seconds
- **After**: Pattern matching takes <1 second
- **Accuracy**: 100% on standard headers
- **Fallback**: LLM extraction for non-standard formats

### 2. Dual Pattern Support
- **Pattern A**: George Padron style (no blank after title)
- **Pattern B**: Robin Michalek style (blank after title)
- **Detection**: Automatic based on Line 2 content
- **Coverage**: Handles all known transcript formats

### 3. Metadata Propagation
- **Early Extraction**: Header metadata available from Parser Agent
- **State Management**: Propagated through AgentState
- **Agent Access**: All downstream agents receive complete context
- **CRM Quality**: Baserow populated with reliable metadata

## Error Handling & Fallbacks

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ERROR HANDLING FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

Header Extraction:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Try Pattern A detection                                                     │
│ 2. Try Pattern B detection                                                     │
│ 3. If both fail → Use LLM extraction (fallback)                               │
│ 4. If LLM fails → Generate minimal metadata from filename                      │
└─────────────────────────────────────────────────────────────────────────────────┘

Pipeline Resilience:
┌─────────────────────────────────────────────────────────────────────────────────┐
│ • Structuring Agent failure → Skip NLP enrichment, continue with basic parsing │
│ • Parser Agent failure → Use filename-based transcript_id, continue           │
│ • Chunker Agent failure → Use simple text splitting, continue                 │
│ • Embedder Agent failure → Skip vector storage, continue with downstream      │
│ • CRM Agent failure → Log error, continue with persistence                    │
│ • Persistence Agent failure → Log error, return partial results               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Integration Points

### 1. Baserow CRM Integration
```
HEADER METADATA → CRM AGENT → BASEROW SYNC
      │              │            │
      ▼              ▼            ▼
[Client Info] → [Transform] → [Upsert]
      │              │            │
      ▼              ▼            ▼
[Meeting Data] → [Field Map] → [Tables]
      │              │            │
      ▼              ▼            ▼
[Transcript ID] → [Validation] → [Clients]
                           │
                           ▼
                      [Meetings]
                           │
                           ▼
                      [Deals]
```

### 2. Neo4j Knowledge Graph
```
HEADER METADATA → KNOWLEDGE ANALYST → NEO4J
      │                  │              │
      ▼                  ▼              ▼
[Client Name] → [Entity Extraction] → [Client Node]
      │                  │              │
      ▼                  ▼              ▼
[Meeting Info] → [Graph Building] → [Meeting Node]
      │                  │              │
      ▼                  ▼              ▼
[Transcript ID] → [Relationships] → [Edges]
```

### 3. Qdrant Vector Store
```
CHUNKS WITH METADATA → EMBEDDER → QDRANT
         │               │         │
         ▼               ▼         ▼
[Header + Dialogue] → [Embed] → [Store]
         │               │         │
         ▼               ▼         ▼
[Metadata] → [Vector] → [Index]
         │               │         │
         ▼               ▼         ▼
[Filtering] → [Search] → [Retrieve]
```

This architecture ensures robust, scalable, and accurate processing of sales meeting transcripts with comprehensive metadata extraction and intelligent fallback mechanisms.
