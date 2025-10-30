# LangFuse Usage Guide - Stellar Sales System

> **Learn how to use LangFuse to monitor, debug, and optimize your pipeline**

This guide teaches you how to interpret LangFuse traces, find performance bottlenecks, and debug pipeline issues.

---

## Table of Contents

1. [Understanding the LangFuse UI](#understanding-the-langfuse-ui)
2. [Running Your First Traced Pipeline](#running-your-first-traced-pipeline)
3. [Interpreting Traces](#interpreting-traces)
4. [Finding Performance Bottlenecks](#finding-performance-bottlenecks)
5. [Debugging Failed Pipelines](#debugging-failed-pipelines)
6. [Filtering and Searching](#filtering-and-searching)
7. [Comparing Pipeline Runs](#comparing-pipeline-runs)
8. [Best Practices](#best-practices)

---

## Understanding the LangFuse UI

### Main Navigation

When you open LangFuse (http://localhost:3000), you'll see:

```
┌─────────────────────────────────────────┐
│  LangFuse                               │
├─────────────────────────────────────────┤
│  📊 Dashboard        │  Main view       │
│  🔍 Traces           │  All pipeline runs│
│  💬 Generations      │  LLM calls       │
│  📁 Sessions         │  Grouped runs    │
│  📈 Metrics          │  Analytics       │
│  ⚙️  Settings         │  Config & keys   │
└─────────────────────────────────────────┘
```

### Key Sections

1. **Traces** (Most Important)
   - Shows all pipeline executions
   - Each row = one complete pipeline run
   - Click to see detailed timeline

2. **Generations**
   - Shows individual LLM calls
   - Useful for tracking token usage
   - See what prompts were sent to the model

3. **Dashboard**
   - Overview of recent activity
   - Performance charts
   - Error rate metrics

---

## Running Your First Traced Pipeline

### Step 1: Start the Enhanced Pipeline

```bash
# Make sure you're in the project directory
cd /path/to/stellar-sales-system

# Activate virtual environment (if using one)
source venv/bin/activate

# Run the enhanced pipeline
python orchestrator/pipeline_langfuse_enhanced.py
```

### Step 2: Watch Console Output

You'll see real-time progress:

```
================================================================================
🚀 STARTING ENHANCED PIPELINE WITH LANGFUSE TRACING
================================================================================
📄 File: pipeline_test.txt
📏 Size: 45678 bytes
🕐 Started: 2025-10-21 14:30:00
================================================================================

✅ Loaded transcript (45678 characters)

🔍 Created LangFuse trace: Pipeline: pipeline_test.txt
   Trace ID: trace_abc123xyz
   View at: http://localhost:3000/trace/trace_abc123xyz

🏃 Running pipeline agents...
   (Watch progress in LangFuse UI for detailed metrics)

────────────────────────────────────────────────────────────────────────────────
✅ Agent 'structuring' completed (#1)
────────────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────────────
✅ Agent 'parser' completed (#2)
   📋 Transcript ID: 20251021-143000
────────────────────────────────────────────────────────────────────────────────

[... more agents ...]

================================================================================
✅ PIPELINE COMPLETED SUCCESSFULLY
================================================================================
```

### Step 3: Open LangFuse UI

Click the trace link from the console output, or:

1. Go to http://localhost:3000
2. Click **"Traces"** in left menu
3. Find your pipeline run (top of the list)

---

## Interpreting Traces

### Trace Overview

When you click on a trace, you'll see:

```
Pipeline: pipeline_test.txt
Status: ✅ Success
Duration: 125.4s
Started: 2025-10-21 14:30:00
```

### Timeline View

The most important view! Shows:

```
┌─────────────────────────────────────────────────────────┐
│  Timeline (hover to see details)                       │
├─────────────────────────────────────────────────────────┤
│  ● Structuring Agent        │████░░░░░░│  2.3s         │
│  ● Parser Agent             │░░██░░░░░░│  1.8s         │
│  ● Chunker Agent            │░░░░█░░░░░│  0.5s         │
│  ● Embedder Agent           │░░░░░███░░│  15.2s        │
│  ● Email Agent              │░░░░░░░██░│  8.1s         │
│  ● Social Agent             │░░░░░░░██░│  7.9s         │
│  ● Sales Coach Agent        │░░░░░░░██░│  8.5s         │
│  ● CRM Agent                │░░░░░░░░██│  42.3s  ⚠️    │
│  ● Persistence Agent        │░░░░░░░░░█│  5.8s         │
└─────────────────────────────────────────────────────────┘
```

**Reading the Timeline:**
- **Horizontal position** = when the agent ran
- **Bar length** = how long it took
- **Color** = status (green=success, red=error, yellow=warning)
- **⚠️ Icon** = Warning or noteworthy behavior

### Agent Details

Click on any agent in the timeline to see:

1. **Input Data**
   ```json
   {
     "file_path": "pipeline_test.txt",
     "transcript_id": "20251021-143000",
     ...
   }
   ```

2. **Output Data**
   ```json
   {
     "chunks": [...],
     "chunks_data": {...},
     ...
   }
   ```

3. **Metadata**
   ```json
   {
     "agent_name": "ChunkerAgent",
     "execution_time_seconds": 0.5,
     "chunks_count": 33,
     "status": "success"
   }
   ```

### LLM Generations

Nested under agents, you'll see LLM calls:

```
CRM Agent
  ↳ LLM Call #1: Extract customer data
     Input Tokens: 15,234
     Output Tokens: 342
     Duration: 38.2s
     Model: deepseek-coder:33b-instruct
```

**Why this matters:**
- Track which agents make expensive LLM calls
- See exact prompts sent to the model
- Understand token usage and costs
- Debug prompt engineering issues

---

## Finding Performance Bottlenecks

### Identifying Slow Agents

Look at the timeline and find the longest bars.

**Example Analysis:**

```
Timeline shows:
  CRM Agent: 42.3s  ← BOTTLENECK!
  Embedder Agent: 15.2s
  Email Agent: 8.1s
  All others: < 3s
```

**Conclusion:** CRM Agent is the bottleneck (42s out of 125s total = 33% of time)

### Investigating Slow Agents

Click on the slow agent (CRM Agent) and check:

1. **LLM Calls**
   - How many LLM calls?
   - How long does each take?
   - Can we reduce prompt size?

2. **Input Size**
   - How much data is being processed?
   - Can we chunk or filter it?

3. **Metadata**
   - Look for clues in custom metrics
   - Check for retries or errors

### Common Bottlenecks

| Agent | Typical Cause | Solution |
|-------|--------------|----------|
| CRM Agent | Large LLM extraction | Switch to faster model for CRM |
| Embedder Agent | Many chunks to embed | Batch embedding calls |
| Parser Agent | Large transcript | Already optimized, just slow file |
| Any Agent | LLM timeout/retry | Check Ollama is running |

### Optimization Strategies

1. **Reduce LLM calls**
   - Combine multiple extractions into one prompt
   - Use REGEX where possible (like CRM Agent does for dollar amounts)

2. **Switch to faster models**
   - CRM: Use Mistral 7B instead of DeepSeek 33B
   - Trade-off: Faster but potentially less accurate

3. **Parallel execution**
   - Email, Social, and Coach agents run in parallel
   - Check graph.py for parallelization opportunities

4. **Caching**
   - If processing same transcript multiple times
   - Cache embeddings and structured data

---

## Debugging Failed Pipelines

### Finding Failed Traces

In the Traces view:

1. **Filter by Status**
   - Click "Filters" button
   - Select "Status: Error"
   - Shows only failed pipelines

2. **Look for red indicators**
   - Failed traces have red ❌ icon
   - Partial failures have yellow ⚠️ icon

### Analyzing Failures

Click on a failed trace to see:

1. **Which agent failed**
   - Timeline shows red bar at failure point
   - Subsequent agents won't run

2. **Error message**
   ```
   Agent: CRM Agent (FAILED)
   Error: ValueError: Invalid date format
   Stack Trace: [full Python traceback]
   ```

3. **Input data that caused failure**
   - See exact data passed to the failing agent
   - Helps reproduce the issue

### Common Failure Patterns

#### 1. LLM Connection Error

**Symptoms:**
```
Error: Connection refused to http://localhost:11434
```

**Cause:** Ollama not running

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve
```

#### 2. Invalid Data Format

**Symptoms:**
```
Error: KeyError: 'transcript_id'
```

**Cause:** Agent expects data that wasn't provided by previous agent

**Solution:**
- Check the agent before the failing one
- Verify it's outputting expected data structure
- Look at the input data in LangFuse

#### 3. LLM Timeout

**Symptoms:**
```
Error: Request timed out after 120 seconds
```

**Cause:** LLM model is too slow or overwhelmed

**Solution:**
- Increase timeout in `core/llm_client.py`
- Switch to faster model
- Reduce input size

#### 4. Out of Memory

**Symptoms:**
```
Error: torch.cuda.OutOfMemoryError
```

**Cause:** Processing very large transcript

**Solution:**
- Process transcript in smaller chunks
- Use CPU instead of GPU for large files
- Increase available memory

### Debugging Workflow

1. **Find the error in LangFuse**
   - Navigate to failed trace
   - Click on red agent bar
   - Read error message and stack trace

2. **Reproduce locally**
   - Use the same transcript file
   - Run enhanced pipeline: `python orchestrator/pipeline_langfuse_enhanced.py`
   - Watch console for same error

3. **Add debug logging**
   - Edit the failing agent
   - Add print statements or logging
   - Run again and watch output

4. **Fix and verify**
   - Make your fix
   - Run pipeline again
   - Check LangFuse shows success (green)

---

## Filtering and Searching

### Basic Filters

On the Traces page, click **"Filters"** to access:

1. **Status**
   - Success: Only successful runs
   - Error: Only failed runs
   - All: Everything

2. **Date Range**
   - Today: Traces from today
   - Last 7 days: Recent traces
   - Custom: Pick specific dates

3. **Name**
   - Filter by trace name (transcript filename)
   - Example: `Pipeline: YONGSIK JOHNG`

### Advanced Search

Use the search bar to find specific traces:

```
# Search by transcript ID
transcript_id:20251021-143000

# Search by client name
client:Yongsik Johng

# Search by error type
error:ValueError

# Search by agent name
agent:CRMAgent
```

### Using Metadata Tags

Our enhanced pipeline adds custom tags:

```json
{
  "pipeline_type": "ingestion",
  "filename": "test.txt",
  "transcript_id": "20251021-143000",
  "pipeline_version": "enhanced_v1"
}
```

**Filter by tag:**
1. Click "Metadata" filter
2. Add key-value pair
3. Example: `pipeline_type = ingestion`

### Organizing Traces

**Best Practices:**

1. **Name traces descriptively**
   - Use client name in filename
   - Include date in filename
   - Example: `2025-10-21_John_Smith_Meeting.txt`

2. **Add custom metadata**
   - Edit `pipeline_langfuse_enhanced.py`
   - Add more metadata fields
   - Example: `deal_stage`, `urgency`, `rep_name`

3. **Use sessions**
   - Group related traces together
   - Example: All traces for one client

---

## Comparing Pipeline Runs

### Why Compare?

- **Performance regression**: Is new code slower?
- **Model comparison**: Is Mistral 7B as good as DeepSeek 33B?
- **Data validation**: Are similar transcripts processed consistently?

### How to Compare

1. **Run pipeline twice**
   ```bash
   # Run 1: With DeepSeek 33B
   LLM_MODEL_NAME=deepseek-coder:33b-instruct python orchestrator/pipeline_langfuse_enhanced.py
   
   # Run 2: With Mistral 7B
   LLM_MODEL_NAME=mistral:7b python orchestrator/pipeline_langfuse_enhanced.py
   ```

2. **Open both traces**
   - In LangFuse, open first trace in one tab
   - Open second trace in another tab
   - Compare side-by-side

3. **Compare metrics**
   
   | Metric | DeepSeek 33B | Mistral 7B | Winner |
   |--------|--------------|------------|--------|
   | Total Time | 125.4s | 78.2s | Mistral ✅ |
   | CRM Accuracy | 95% | 88% | DeepSeek ✅ |
   | Token Cost | $0.45 | $0.12 | Mistral ✅ |

### Automated Comparison (Advanced)

You can use LangFuse API to fetch and compare traces programmatically:

```python
from langfuse import Langfuse

langfuse = Langfuse()

# Get recent traces
traces = langfuse.get_traces(limit=10)

# Compare execution times
for trace in traces:
    print(f"{trace.name}: {trace.duration}s")
```

---

## Best Practices

### 1. Always Use Descriptive Filenames

**Good:**
```
2025-10-21_George_Padron_Estate_Planning.txt
2025-10-22_Linda_Barnes_Trust_Review.txt
```

**Bad:**
```
transcript1.txt
test.txt
meeting_notes.txt
```

**Why:** Makes traces easy to find and identify in LangFuse

### 2. Check LangFuse After Every Pipeline Change

Workflow:
1. Make code change
2. Run pipeline: `python orchestrator/pipeline_langfuse_enhanced.py`
3. Check LangFuse for any red flags
4. Compare execution time with baseline

**Why:** Catch performance regressions early

### 3. Keep Traces Organized

- **Delete old test traces** periodically
- **Add custom metadata** for important runs
- **Use sessions** to group related traces

### 4. Monitor Key Metrics

Track these over time:

- **Average pipeline duration**: Should be stable
- **Error rate**: Should be < 5%
- **LLM token usage**: Watch for unexpected spikes
- **Agent success rates**: Each agent should be > 95%

### 5. Document Interesting Findings

When you find something interesting:

1. **Take screenshots** of LangFuse trace
2. **Note the trace ID** for future reference
3. **Document in project notes** or tickets
4. **Share with team** if relevant

### 6. Use LangFuse for Code Reviews

Before merging code:

1. Run pipeline with new code
2. Get trace ID
3. Add to pull request: "LangFuse trace: trace_abc123"
4. Reviewers can verify performance impact

---

## Quick Reference

### Common Tasks

| Task | How To |
|------|--------|
| View all traces | http://localhost:3000/traces |
| Find failed runs | Traces → Filter → Status: Error |
| See LLM calls | Click trace → Generations tab |
| Compare runs | Open two traces in separate tabs |
| Search by client | Search bar: `client:Name` |
| Export data | Trace → ... menu → Export JSON |

### Key Metrics to Watch

- **Total Duration**: How long pipeline took
- **Agent Times**: Time per agent
- **LLM Tokens**: Input + output tokens
- **Error Rate**: % of failed traces
- **Data Quality**: Verify outputs are correct

### Keyboard Shortcuts

- `Ctrl+K` or `Cmd+K`: Quick search
- `r`: Refresh traces
- `←` `→`: Navigate between traces
- `Esc`: Close detail panel

---

## Next Steps

Now that you understand LangFuse:

1. **Run your first real pipeline**
   - Use an actual transcript
   - Analyze the results
   - Look for bottlenecks

2. **Read the Troubleshooting Guide**
   - `docs/LANGFUSE_TROUBLESHOOTING.md`
   - Solutions to common problems

3. **Experiment with filters**
   - Try different search queries
   - Create custom metadata
   - Organize your traces

4. **Share knowledge with your team**
   - Show them how to use LangFuse
   - Create team conventions
   - Document findings

---

## Summary

**Key Takeaways:**

1. **Timeline view** is your best friend for understanding pipeline flow
2. **Compare traces** to measure impact of changes
3. **Filter and search** to find specific runs
4. **Monitor key metrics** to track system health
5. **Debug with context** using full input/output data

**Remember:**
- LangFuse is a tool, not a solution
- Use it to inform decisions, not replace testing
- The best optimization is the one you measure

---

**Need Help?**
- Troubleshooting: `docs/LANGFUSE_TROUBLESHOOTING.md`
- Setup Issues: `docs/LANGFUSE_SETUP.md`
- LangFuse Docs: https://langfuse.com/docs


