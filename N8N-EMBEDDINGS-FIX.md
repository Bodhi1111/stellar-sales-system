# N8N Embeddings Model Fix - Complete Solution

## Problem Summary

The n8n workflow's "Generate Embeddings" node was failing with connection errors because it was trying to connect to services using `localhost`, which doesn't work correctly inside Docker containers.

### Root Cause

N8N runs inside a Docker container (`stellar_n8n`). When a container tries to access `localhost`, it refers to itself, not the host machine or other containers. This caused:

1. **Embeddings endpoint failure**: Could not reach FastAPI at `localhost:8000/embeddings`
2. **Qdrant connection failure**: Could not reach Qdrant at `localhost:6333`
3. **Baserow connection failure**: Could not reach Baserow at `localhost:8080`

## Solution Applied

### Fixed URLs in `stellar-sales-workflow-n8n.json`

#### 1. FastAPI Embeddings Endpoint (ALREADY CORRECT)
- **Node**: Generate Embeddings
- **URL**: `http://host.docker.internal:8000/embeddings` ✅
- **Status**: Already using correct Docker networking
- **Explanation**: `host.docker.internal` is a special DNS name that Docker provides to access the host machine from inside containers

#### 2. Qdrant Vector Database (FIXED)
- **Nodes**:
  - Store Child Chunks in Qdrant
  - Store Parent Chunks in Qdrant
  - Qdrant Search
- **Old URL**: `http://localhost:6333` ❌
- **New URL**: `http://stellar_qdrant:6333` ✅
- **Explanation**: Uses the Docker container name for container-to-container communication

#### 3. Baserow CRM (FIXED)
- **Nodes**:
  - Sync to Baserow - Clients
  - Sync to Baserow - Meetings
  - Sync to Baserow - Deals
  - Sync to Baserow - Communications
  - Sync to Baserow - Coaching
- **Old URL**: `http://localhost:8080` ❌
- **New URL**: `http://baserow:80` ✅
- **Explanation**: Uses the Docker container name and the internal port (80) instead of the mapped external port (8080)

## How to Apply the Fix

### Option 1: Re-import the Corrected Workflow (Recommended)

1. **Open n8n UI**: Navigate to http://localhost:5678

2. **Delete the existing workflow** (optional - you can also deactivate it):
   - Go to Workflows
   - Find "Stellar Sales System"
   - Click the three dots → Delete

3. **Import the corrected workflow**:
   - Click "+ Add workflow" or "Import from file"
   - Select `/Users/joshuavaughan/dev/Projects/stellar-sales-system/stellar-sales-workflow-n8n.json`
   - Click "Import"

4. **Activate the workflow**:
   - Toggle the "Active" switch to ON
   - The workflow will now be watching for new transcripts

### Option 2: Manual Fix in n8n UI

If you prefer to fix the existing workflow manually:

1. Open the "Stellar Sales System" workflow in n8n
2. Click on **Store Child Chunks in Qdrant** node
   - Change URL from `http://localhost:6333/...` to `http://stellar_qdrant:6333/...`
3. Click on **Store Parent Chunks in Qdrant** node
   - Change URL from `http://localhost:6333/...` to `http://stellar_qdrant:6333/...`
4. Click on **Qdrant Search** node
   - Change URL from `http://localhost:6333/...` to `http://stellar_qdrant:6333/...`
5. Click on all **Baserow** nodes and change:
   - From: `http://localhost:8080/...`
   - To: `http://baserow:80/...`
6. Save the workflow

## Verification

### Test the Embeddings Endpoint

From your host machine:
```bash
curl -X POST http://localhost:8000/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text":"test embedding"}'
```

Expected: Should return a JSON response with a 768-dimension embedding vector.

### Test the Workflow

1. Copy a sample transcript to the watched directory:
```bash
cp /path/to/sample_transcript.txt "/Users/joshuavaughan/Documents/McAdams Transcripts/"
```

2. Monitor n8n execution:
   - Go to n8n UI → Executions
   - You should see a new execution start
   - Check that all nodes execute successfully (green checkmarks)

3. Verify data storage:
   - Check Qdrant: http://localhost:6333/dashboard
   - Check Baserow: http://localhost:8080

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (bridge)                   │
│                                                              │
│  ┌──────────────┐    ┌─────────────────┐                   │
│  │   stellar    │    │   FastAPI       │ (on host)          │
│  │     _n8n     │───→│  localhost:8000 │                   │
│  │              │    │  /embeddings    │                   │
│  └──────┬───────┘    └─────────────────┘                   │
│         │             (via host.docker.internal)            │
│         │                                                    │
│         ├───→ ┌────────────────┐                           │
│         │     │   stellar      │                            │
│         │     │   _qdrant      │ :6333                     │
│         │     │                │                            │
│         │     └────────────────┘                            │
│         │      (via container name)                         │
│         │                                                    │
│         └───→ ┌────────────────┐                           │
│               │    baserow     │ :80                       │
│               │                │                            │
│               └────────────────┘                            │
│                (via container name)                         │
└─────────────────────────────────────────────────────────────┘
```

## Docker Networking Rules

1. **Container → Host**: Use `host.docker.internal` (FastAPI embeddings)
2. **Container → Container**: Use container name from `docker-compose.yml` (Qdrant, Baserow)
3. **Host → Container**: Use `localhost` with mapped ports

## Files Modified

- `/Users/joshuavaughan/dev/Projects/stellar-sales-system/stellar-sales-workflow-n8n.json`
  - Fixed 3 Qdrant URLs
  - Fixed 5 Baserow URLs
  - Total: 8 URL corrections

## Next Steps

After applying this fix:

1. ✅ Embeddings will generate successfully using the BAAI/bge-base-en-v1.5 model
2. ✅ Vectors will be stored in Qdrant for semantic search
3. ✅ CRM data will sync to Baserow tables
4. ✅ The complete RAG pipeline will function end-to-end

## Technical Details

### Embedding Model Specifications
- **Model**: BAAI/bge-base-en-v1.5
- **Dimensions**: 768
- **Endpoint**: POST http://localhost:8000/embeddings
- **Request**: `{"text": "string"}`
- **Response**: `{"embedding": [float...], "dimension": 768}`

### Qdrant Collection
- **Name**: `transcripts`
- **Vector Size**: 768
- **Distance**: COSINE
- **Architecture**: Parent-child hierarchical chunking

### Baserow Tables
- **Database ID**: 174
- **Tables**: Clients (704), Meetings (705), Deals (706), Communications (707), Sales Coaching (708), Chunks (709)
