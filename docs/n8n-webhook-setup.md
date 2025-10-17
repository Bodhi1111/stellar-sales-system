# N8N Webhook Trigger Setup Guide

This guide explains how to set up the N8N workflow with webhook trigger for reliable, instant testing and visual monitoring.

## Problem Solved

**Before:** File Watcher trigger had limitations:
- Only detects files added AFTER workflow activation
- Polling delay (30-60 seconds)
- Doesn't work in manual test mode
- Cannot trigger on-demand

**After:** Webhook trigger provides:
- ✅ Instant triggering (no polling delay)
- ✅ Visual monitoring in N8N UI
- ✅ On-demand testing via Python script
- ✅ Dual mode (automated + manual)

## Architecture

```
┌─ Webhook Trigger ──→ Process File ─┐
│                                      ├→ Parse → Chunk → Embed → RAG → Baserow
└─ File Watcher ──→ Read File ────────┘
           ↓
      Merge Triggers
```

## Setup Instructions

### Step 1: Import Updated Workflow to N8N

**Option A: Via N8N UI (Recommended)**

1. Open N8N UI: http://localhost:5678
2. Click "Workflows" in sidebar
3. Click "+ Add workflow" (or open existing "Stellar Sales System")
4. Click the 3-dot menu → "Import from File"
5. Select `stellar-sales-workflow-n8n-webhook.json`
6. Click "Save" and "Activate"

**Option B: Via N8N CLI**

```bash
# Copy workflow file to N8N data directory
docker cp stellar-sales-workflow-n8n-webhook.json stellar_n8n:/data/workflows/

# Restart N8N to load new workflow
docker restart stellar_n8n
```

### Step 2: Configure Webhook URL

The webhook will be automatically available at:

```
http://localhost:5678/webhook/stellar-sales-webhook
```

**Verify webhook is active:**
```bash
curl -X GET http://localhost:5678/webhook/stellar-sales-webhook
# Should return: {"message": "Webhook endpoint ready"}
```

### Step 3: Test the Webhook

**Quick Test (Bash):**
```bash
./scripts/test_n8n_webhook.sh
```

**Manual Test (Python):**
```bash
./venv/bin/python scripts/trigger_n8n_workflow.py \
  --file data/transcripts/test_sprint01.txt
```

**Custom File:**
```bash
./venv/bin/python scripts/trigger_n8n_workflow.py \
  --file /path/to/your/transcript.txt
```

## Visual Monitoring

Once triggered, you can watch the workflow execute in real-time:

### N8N UI Dashboard
1. Open: http://localhost:5678
2. Click "Executions" tab (left sidebar)
3. Select the most recent execution
4. Watch nodes light up green as they complete
5. Click any node to see input/output data

### View Results

**Qdrant Dashboard:**
```bash
open http://localhost:6333/dashboard
```
- See vector embeddings stored
- Browse collections and points

**Baserow CRM:**
```bash
open http://localhost:8080
```
- View client records
- Check meeting details
- See CRM data populated

## Workflow Nodes Explained

### Entry Points (Parallel Triggers)

**1. Webhook Trigger**
- Type: `n8n-nodes-base.webhook`
- Path: `/stellar-sales-webhook`
- Method: `POST`
- **Use:** Manual/on-demand testing

**2. File Watcher**
- Type: `n8n-nodes-base.localFileTrigger`
- Path: `/transcripts`
- Polling: `true`
- **Use:** Automated production monitoring

### Processing Nodes

**3. Process Webhook File**
- Converts webhook upload to File Watcher format
- Ensures both triggers have identical output

**4. Read Transcript File**
- Reads files detected by File Watcher

**5. Merge Triggers**
- Combines both trigger paths
- Single output stream to Parse Transcript

**6. Parse Transcript → Chunker → Embedder → RAG → Baserow**
- (Existing pipeline nodes - no changes)

## Usage Examples

### Development Workflow

```bash
# 1. Start services
make docker-up

# 2. Verify N8N is running
curl http://localhost:5678/healthz

# 3. Trigger workflow with test file
./scripts/test_n8n_webhook.sh

# 4. Open N8N UI to watch execution
open http://localhost:5678

# 5. Check results in Baserow
open http://localhost:8080
```

### Production Workflow

```bash
# Copy transcript to watched folder
docker exec -i stellar_n8n sh -c 'cat > /transcripts/new_file.txt' < transcript.txt

# File Watcher will auto-detect within 30-60 seconds
# Check executions in N8N UI
```

### Batch Processing

```python
#!/usr/bin/env python3
from pathlib import Path
import subprocess

transcripts_dir = Path("data/transcripts")

for transcript in transcripts_dir.glob("*.txt"):
    print(f"Processing: {transcript.name}")
    subprocess.run([
        "./venv/bin/python",
        "scripts/trigger_n8n_workflow.py",
        "--file", str(transcript)
    ])
```

## Troubleshooting

### Webhook Not Found (404)

**Problem:** `curl http://localhost:5678/webhook/stellar-sales-webhook` returns 404

**Solution:**
1. Check workflow is activated in N8N UI
2. Verify webhook node exists with correct path
3. Restart N8N: `docker restart stellar_n8n`

### Workflow Not Executing

**Problem:** Webhook returns 200 but nothing happens

**Solution:**
1. Check N8N executions tab for errors
2. Verify all services are running:
   ```bash
   docker ps | grep -E "(postgres|qdrant|ollama|baserow)"
   ```
3. Check N8N logs:
   ```bash
   docker logs stellar_n8n --tail 50
   ```

### File Too Large

**Problem:** Large transcripts (>60KB) cause timeouts

**Solution:**
1. Use smaller test files (< 10KB)
2. Switch to DeepSeek 33B model for larger context:
   ```bash
   # Update .env
   LLM_MODEL_NAME=deepseek-coder:33b-instruct
   ```

## API Reference

### Webhook Endpoint

**URL:** `POST http://localhost:5678/webhook/stellar-sales-webhook`

**Request (multipart/form-data):**
```bash
curl -X POST http://localhost:5678/webhook/stellar-sales-webhook \
  -F "data=@transcript.txt" \
  -F "filename=transcript.txt"
```

**Request (Python):**
```python
import requests

with open('transcript.txt', 'r') as f:
    files = {'data': (f.name, f, 'text/plain')}
    response = requests.post(
        'http://localhost:5678/webhook/stellar-sales-webhook',
        files=files
    )
```

**Response (200 OK):**
```json
{
  "success": true,
  "execution_id": "abc123",
  "message": "Workflow triggered"
}
```

## Best Practices

### Development
- Use webhook trigger for rapid testing
- Keep test transcripts small (<10KB)
- Monitor N8N UI for real-time feedback

### Production
- Use File Watcher for automated processing
- Keep webhook as backup/manual override
- Set up monitoring on N8N executions

### Testing
- Test with known-good transcripts first
- Verify results in Qdrant and Baserow
- Check LLM model context limits

## Next Steps

1. ✅ Import workflow to N8N
2. ✅ Test webhook trigger
3. ✅ Monitor execution in N8N UI
4. ✅ Validate results in databases
5. 🔄 Process your transcripts!

---

**Need Help?**
- N8N Docs: https://docs.n8n.io
- Project Issues: https://github.com/your-repo/issues
- Stellar Sales System: See [CLAUDE.md](../CLAUDE.md)
