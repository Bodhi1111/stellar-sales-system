# Visual Debugging Setup Guide for Stellar Sales System

## TL;DR - What You Should Actually Do

**Skip Flowise. Use these instead:**

1. **LangGraph Studio** (2 hours) → Visual workflow design & debugging
2. **Langfuse** (4 hours) → Production observability & monitoring

Total investment: **1 day**  
Benefit: Professional-grade visual debugging for your existing LangGraph workflows

---

## Why Not Flowise?

**Flowise is for LangChain (simple chains). You use LangGraph (complex state machines).**

Your workflows have features Flowise cannot represent:
- ❌ Conditional routing (router functions that decide next step dynamically)
- ❌ Self-correcting loops (Auditor → Replanner → Planner)
- ❌ Complex state accumulation (AgentState with 20+ fields)
- ❌ Parallel fan-out/fan-in (multiple edges from one node)

**Migration would require 4-6 weeks to rewrite everything and lose critical capabilities.**

See [FLOWISE_INTEGRATION_EVALUATION.md](./FLOWISE_INTEGRATION_EVALUATION.md) for full analysis.

---

## Option 1: LangGraph Studio ⭐ BEST FOR DEVELOPMENT

### What It Does
- Visualizes your actual LangGraph workflows (nodes, edges, conditional routes)
- Step-through debugging (pause at any node, inspect state)
- Time-travel (replay with different inputs)
- Shows why router picked a specific path

### Setup (30 minutes)

```bash
# 1. Install
cd /workspace
./venv/bin/pip install langgraph-cli

# 2. Create config file
cat > langgraph.json << 'EOF'
{
  "graphs": {
    "ingestion": {
      "path": "orchestrator/graph.py",
      "graph": "app"
    },
    "reasoning": {
      "path": "orchestrator/graph.py", 
      "graph": "reasoning_app"
    }
  }
}
EOF

# 3. Launch Studio
langgraph dev orchestrator/graph.py
# Opens at http://localhost:8123
```

### Usage
1. Open http://localhost:8123 in browser
2. Select "ingestion" or "reasoning" workflow
3. Click "Run" and provide test input
4. Watch nodes turn green as they execute
5. Click any node to inspect:
   - Input state
   - Output state  
   - Execution time
   - Errors (if any)

### Example: Debug Reasoning Loop
```
1. Run query: "What objections did the client raise?"
2. Watch execution:
   - Gatekeeper → (passes, no clarification needed)
   - Planner → (creates 3-step plan)
   - Tool Executor → (runs sales_copilot_tool)
   - Auditor → (confidence: 2/5 - LOW!)
   - Router → (routes to "replanner" because confidence < 3)
   - Replanner → (clears plan)
   - Planner → (creates NEW 2-step plan)
   - Tool Executor → (runs again with better query)
   - Auditor → (confidence: 4/5 - GOOD!)
   - Router → (routes to "strategist")
   - Strategist → (synthesizes final answer)
3. Click "Replanner" node to see why it was triggered
4. Compare both plans to see how it improved
```

**This visualization shows your ACTUAL workflow logic that Flowise cannot represent.**

---

## Option 2: Langfuse ⭐ BEST FOR PRODUCTION

### What It Does
- Traces every LLM call and agent execution
- Tracks costs, tokens, latency
- Dashboard showing success/failure rates
- Self-hosted (open source, no cloud dependency)

### Setup (2-3 hours)

#### Step 1: Add to Docker (5 minutes)
```yaml
# Add to docker-compose.yml after existing services
  langfuse:
    image: langfuse/langfuse:latest
    container_name: stellar_langfuse
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/langfuse
      NEXTAUTH_SECRET: changeme-generate-random-string
      NEXTAUTH_URL: http://localhost:3000
      SALT: changeme-generate-salt
    depends_on:
      - postgres
```

#### Step 2: Initialize Database (5 minutes)
```bash
make docker-up
# Wait for Langfuse to start, then visit http://localhost:3000
# Follow setup wizard to create account
```

#### Step 3: Get API Keys (2 minutes)
1. Visit http://localhost:3000/settings
2. Create new project: "stellar-sales-system"
3. Copy: Public Key + Secret Key

#### Step 4: Integrate with Code (30 minutes)

**Add to .env:**
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

**Update config/settings.py:**
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Langfuse Settings
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"
```

**Create core/observability.py:**
```python
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from config.settings import settings

# Initialize Langfuse
langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)

def get_langfuse_handler(trace_name: str):
    """Get Langfuse callback handler for tracing"""
    return CallbackHandler(
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        secret_key=settings.LANGFUSE_SECRET_KEY,
        host=settings.LANGFUSE_HOST,
        trace_name=trace_name
    )
```

**Update orchestrator/pipeline.py:**
```python
from core.observability import get_langfuse_handler

async def run_pipeline(file_path: Path):
    """Run pipeline with Langfuse tracing"""
    print(f"--- Starting Advanced Pipeline for {file_path.name} ---")
    
    # Create trace
    handler = get_langfuse_handler(f"ingestion_{file_path.stem}")
    
    try:
        raw_text = file_path.read_text(encoding='utf-8')
        initial_state = {"file_path": file_path, "raw_text": raw_text}
        
        final_state = None
        async for event in app.astream(initial_state, config={"callbacks": [handler]}):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")
                if final_state is None:
                    final_state = value.copy() if value else {}
                else:
                    if value:
                        final_state.update(value)
        
        print("--- Advanced Pipeline Finished ---")
        return final_state
    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise
    finally:
        handler.flush()  # Ensure traces are sent
```

#### Step 5: Test (5 minutes)
```bash
# Run a test transcript
./venv/bin/python scripts/test_pipeline_quick.py

# Visit http://localhost:3000/traces
# You should see the full execution trace!
```

### Usage

#### Dashboard (http://localhost:3000)
- **Traces**: See every pipeline run with full details
- **Sessions**: Group related runs (e.g., all transcripts from one client)
- **Metrics**: Token usage, costs, latency per agent
- **Errors**: Filter for failed runs, see stack traces

#### Example Insights
```
Query: "Which agents are slowest?"
Answer (from Langfuse):
  - KnowledgeAnalystAgent: avg 44s (bottleneck!)
  - StructuringAgent: avg 28s
  - ParserAgent: avg 12s
  
Action: Optimize KnowledgeAnalystAgent or remove from critical path
```

```
Query: "What's my daily LLM cost?"
Answer (from Langfuse):
  - Today: $2.34 (12 transcripts × $0.195 each)
  - This month: $87.50
  - Top cost: DeepSeek-Coder 33B (95% of total)
```

---

## Quick Comparison

| Feature | Flowise | LangGraph Studio | Langfuse |
|---------|---------|------------------|----------|
| **Visualize workflows** | ❌ (wrong framework) | ✅✅✅ | ✅ |
| **Step-through debug** | ❌ | ✅✅✅ | ⚠️ (post-mortem) |
| **Production monitoring** | ❌ | ⚠️ (dev only) | ✅✅✅ |
| **Cost tracking** | ❌ | ❌ | ✅✅✅ |
| **Open source** | ✅ | ⚠️ (beta/free) | ✅ |
| **Works with LangGraph** | ❌ | ✅✅✅ | ✅✅✅ |
| **Setup time** | N/A | 30 min | 3 hours |

---

## What About Just Using Print Statements?

**That's what you're doing now, and it has serious limitations:**

### Current Debugging (Print Statements)
```python
async def email_node(state: AgentState) -> Dict[str, Any]:
    print("📧 Generating email draft...")
    email_draft = await email_agent.run(...)
    print(f"✅ Email generated: {len(email_draft)} chars")
    return {"email_draft": email_draft}
```

**Problems**:
- ❌ No visibility into LLM internals (prompts, tokens, latency)
- ❌ Hard to trace failures across 10+ agents
- ❌ Can't compare runs (which was faster? which used more tokens?)
- ❌ No aggregate metrics (average pipeline time? failure rate?)
- ❌ Logs disappear unless you save them

### With LangGraph Studio
- ✅ See exact state at each node
- ✅ Visual graph shows execution path
- ✅ Time-travel: replay with different inputs
- ✅ Inspect why conditional routing chose a path

### With Langfuse
- ✅ Every run saved with full details
- ✅ Compare runs side-by-side
- ✅ Aggregate metrics dashboard
- ✅ Alert on errors/slowness
- ✅ Share traces with team (link to specific run)

---

## Recommended Setup Order

### Week 1: LangGraph Studio (Development)
**Investment**: 2-4 hours  
**Benefit**: Immediately understand your complex workflows

1. Install CLI and create config (30 min)
2. Explore ingestion workflow (1 hour)
3. Debug reasoning workflow loops (1 hour)
4. Document findings for team (1 hour)

### Week 2: Langfuse (Production)
**Investment**: 4-6 hours  
**Benefit**: Monitor all production runs, track costs

1. Add to Docker and initialize (1 hour)
2. Integrate with pipelines (2 hours)
3. Set up dashboards (1 hour)
4. Configure alerts (30 min)
5. Team training (30 min)

### Week 3: Documentation
**Investment**: 2-3 hours  
**Benefit**: Team can use tools effectively

1. Add screenshots to README
2. Create debugging playbook
3. Document common issues + solutions

---

## Cost Analysis

| Solution | Setup Time | Ongoing Cost | Value |
|----------|------------|--------------|-------|
| **Flowise** | 4-6 weeks (rewrite) | Complexity debt | ❌ Negative |
| **Print Statements** | 0 (current) | Developer time | ⚠️ Limited |
| **LangGraph Studio** | 2-4 hours | $0 | ✅✅✅ High |
| **Langfuse** | 4-6 hours | $0 (self-hosted) | ✅✅✅ High |

**ROI**: 1 day investment → Permanent improvement in debugging & monitoring

---

## Common Questions

### Q: Can I use both Studio and Langfuse?
**A**: Yes! Recommended setup:
- **Studio**: Local development, debugging complex logic
- **Langfuse**: Production monitoring, cost tracking, team collaboration

### Q: Does this work with DeepSeek-Coder 33B (Ollama)?
**A**: Yes! Both tools work with any LLM (OpenAI, Ollama, Anthropic, etc.)

### Q: Will this slow down my pipeline?
**A**: 
- Studio: No (only when you're actively debugging)
- Langfuse: Minimal (~50-100ms overhead per run for HTTP trace upload)

### Q: What if I don't want to self-host Langfuse?
**A**: Use **LangSmith** (LangChain's official SaaS):
- Free tier: 10k traces/month
- $39/month for production
- Same features, zero setup (just API key)

### Q: Can non-technical users use these tools?
**A**: 
- Studio: Somewhat (can see workflow, but need Python knowledge to modify)
- Langfuse: Yes (stakeholders can view dashboards, no coding needed)

---

## Next Steps

1. **Read full evaluation**: [FLOWISE_INTEGRATION_EVALUATION.md](./FLOWISE_INTEGRATION_EVALUATION.md)
2. **Try LangGraph Studio today**: Follow "Option 1" above (30 minutes)
3. **Schedule Langfuse setup**: Block 4 hours next week
4. **Share this doc with team**: Get feedback on priorities

---

## Support Resources

- **LangGraph Studio**: https://langchain-ai.github.io/langgraph/cloud/
- **Langfuse Docs**: https://langfuse.com/docs
- **LangSmith** (SaaS alternative): https://smith.langchain.com/
- **Community**: LangChain Discord has #langgraph and #langfuse channels

---

**Document Version**: 1.0  
**Date**: 2025-10-21  
**Last Updated**: 2025-10-21  
**Status**: Ready to implement
