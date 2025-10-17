# N8N Webhook Trigger - Quick Start

Visual pipeline monitoring with instant workflow triggering.

## 🚀 Quick Start (3 Steps)

### 1. Import Workflow to N8N

Open N8N UI and import the webhook-enabled workflow:

```bash
# Open N8N
open http://localhost:5678

# Import workflow file:
# stellar-sales-workflow-n8n-webhook.json
```

**Steps in N8N UI:**
1. Click "Workflows" → "+ Add workflow"
2. Click 3-dot menu → "Import from File"
3. Select `stellar-sales-workflow-n8n-webhook.json`
4. Click "Save" and "Activate" ✅

### 2. Trigger Workflow with Test File

```bash
./scripts/test_n8n_webhook.sh
```

**Or manually:**
```bash
./venv/bin/python scripts/trigger_n8n_workflow.py \
  --file data/transcripts/test_sprint01.txt
```

### 3. Watch Execution in N8N UI

```bash
open http://localhost:5678
```

Click "Executions" tab → Watch nodes turn green! 🟢

---

## 📊 What You Get

### Instant Triggering
- **Before:** File Watcher polls every 30-60s
- **After:** Webhook triggers instantly ⚡

### Visual Monitoring
- See each node execute in real-time
- Click nodes to inspect data
- Debug issues immediately

### Dual Mode Operation
- **Webhook:** Manual testing & development
- **File Watcher:** Automated production monitoring

---

## 📁 Files Created

```
scripts/
├── trigger_n8n_workflow.py   # Python trigger script
└── test_n8n_webhook.sh        # Quick test wrapper

stellar-sales-workflow-n8n-webhook.json  # Updated workflow

docs/
└── n8n-webhook-setup.md       # Complete setup guide
```

---

## 🔧 Architecture

```
Entry Points (Parallel):
┌─────────────────┐     ┌──────────────┐
│ Webhook Trigger │     │ File Watcher │
│  (on-demand)    │     │ (automated)  │
└────────┬────────┘     └──────┬───────┘
         │                     │
         ├─────────┬───────────┤
                   │
           ┌───────▼────────┐
           │ Merge Triggers │
           └───────┬────────┘
                   │
         ┌─────────▼──────────┐
         │  Parse Transcript  │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │ Semantic Chunker   │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   Generate          │
         │   Embeddings        │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Store in Qdrant   │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   RAG Search       │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │ Aggregate CRM Data │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Sync to Baserow   │
         │  (5 tables)        │
         └────────────────────┘
```

---

## 💡 Usage Examples

### Test with Sample File
```bash
./scripts/test_n8n_webhook.sh
```

### Process Custom Transcript
```bash
./venv/bin/python scripts/trigger_n8n_workflow.py \
  --file /path/to/transcript.txt
```

### Batch Process Multiple Files
```bash
for file in data/transcripts/*.txt; do
  echo "Processing: $file"
  ./venv/bin/python scripts/trigger_n8n_workflow.py --file "$file"
  sleep 5  # Wait between requests
done
```

---

## 🔍 View Results

### N8N Execution Dashboard
```bash
open http://localhost:5678
```
- Click "Executions" tab
- View real-time progress
- Inspect node data

### Qdrant Vector Database
```bash
open http://localhost:6333/dashboard
```
- Browse collections
- View embedded vectors
- Check points stored

### Baserow CRM
```bash
open http://localhost:8080
```
- Client records
- Meeting details
- CRM insights

---

## 🐛 Troubleshooting

### Webhook Not Found (404)
```bash
# Check N8N is running
curl http://localhost:5678/healthz

# Verify workflow is activated
# (Green toggle in N8N UI)
```

### No Execution Visible
```bash
# Check N8N logs
docker logs stellar_n8n --tail 50

# Verify services running
docker ps
```

### File Too Large (Timeout)
Use smaller test files (<10KB) or switch to DeepSeek model:
```bash
# Edit .env
LLM_MODEL_NAME=deepseek-coder:33b-instruct
```

---

## 📚 Full Documentation

See [docs/n8n-webhook-setup.md](docs/n8n-webhook-setup.md) for:
- Detailed setup instructions
- API reference
- Advanced configuration
- Best practices

---

## ✅ Verification Checklist

- [ ] N8N running at http://localhost:5678
- [ ] Workflow imported and activated
- [ ] Webhook accessible at `/stellar-sales-webhook`
- [ ] Test script executes successfully
- [ ] Execution visible in N8N UI
- [ ] Results appear in Qdrant dashboard
- [ ] CRM data synced to Baserow

---

**🎉 You're Ready!**

The N8N workflow now supports both automated file watching AND instant webhook triggering for the best of both worlds.

Need help? See [docs/n8n-webhook-setup.md](docs/n8n-webhook-setup.md)
