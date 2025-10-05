# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stellar Sales System is a multi-agent sales intelligence platform built with FastAPI and LangGraph. It processes sales transcripts through a sophisticated pipeline of specialized agents, extracting insights and generating actionable outputs for CRM integration, email drafts, social content, and coaching feedback.

## Architecture

The system implements a **dual workflow architecture** with two independent LangGraph workflows:

### Workflow 1: Ingestion Pipeline (Sprint 01)
**Purpose**: Process sales transcripts into structured data and store in databases

**Flow**:
1. **Sequential Processing**: Parser → Structuring → Chunker
2. **Intelligence First (Parallel)**: Knowledge Analyst (Neo4j) + Embedder (Qdrant)
3. **Legacy Downstream**: Email, Social, Sales Coach agents
4. **CRM Aggregation**: Consolidate all insights
5. **Persistence**: Save to PostgreSQL with upsert by `external_id`

**Entry Point**: `file_path` in AgentState
**Export**: `app = create_master_workflow()`

### Workflow 2: Reasoning Engine (Sprint 02)
**Purpose**: Answer user queries through dynamic planning, execution, and self-correction

**Flow**:
```
Gatekeeper (ambiguity check)
    ↓
Planner (create execution plan)
    ↓
Tool Executor → Auditor → Router
    ↑                        ↓
Replanner (if low confidence) ← (decision logic)
                             ↓
                        Strategist (synthesize answer)
```

**Cognitive Nodes**:
- **GatekeeperAgent**: Validates query clarity, requests clarification if ambiguous
- **PlannerAgent**: Decomposes request into step-by-step tool calls
- **Tool Executor**: Executes specialist tools (sales_copilot, crm, email)
- **AuditorAgent**: Verifies tool outputs with confidence scores (1-5)
- **Router**: Pure function routing to next step, replanner, or strategist
- **StrategistAgent**: Synthesizes final answer from all intermediate steps

**Entry Point**: `original_request` in AgentState
**Export**: `reasoning_app = create_reasoning_workflow()`

### Database Architecture
- **PostgreSQL**: Primary relational database for structured data
- **Qdrant**: Vector database for embeddings and semantic search
- **Neo4j**: Graph database for relationship mapping and knowledge graphs

### Key Components
- **Agent State** (`orchestrator/state.py`): TypedDict carrying data through the graph pipeline
- **Settings** (`config/settings.py`): Pydantic settings managing all configuration
- **API** (`api/app.py`): FastAPI endpoint for transcript uploads and processing

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
make install

# Start all database services (PostgreSQL, Qdrant, Neo4j, Ollama)
make docker-up

# Stop all services
make docker-down

# Initialize database tables
./venv/bin/python scripts/init_db.py

# Run the API server
make run-api
# Or directly:
./venv/bin/uvicorn api.app:app --reload
```

### Database Management
```bash
# Test database connection
./venv/bin/python scripts/test_db.py

# Access services:
# - PostgreSQL: localhost:5432
# - Qdrant UI: http://localhost:6333/dashboard
# - Neo4j Browser: http://localhost:7474
# - Ollama API: http://localhost:11434
```

### Testing Workflows
```bash
# Test ingestion pipeline (Sprint 01)
./venv/bin/python orchestrator/pipeline.py

# Test reasoning engine (Sprint 02)
./venv/bin/python scripts/test_reasoning_workflow.py
./venv/bin/python scripts/test_reasoning_complete.py
./venv/bin/python scripts/test_reasoning_simple.py
```

## Agent Development

Each agent follows a consistent pattern in `agents/{agent_name}/{agent_name}_agent.py`:
- Inherits from a base agent class
- Implements an async `run()` method
- Accepts specific inputs from AgentState
- Returns data to be merged back into AgentState

To add a new agent:
1. Create agent module in `agents/` directory
2. Import and initialize in `orchestrator/graph.py`
3. Add node function and workflow edges
4. Update `orchestrator/state.py` with new state fields if needed

## Configuration

Environment variables (`.env`):
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: PostgreSQL credentials
- **LLM configuration**: Ollama with **DeepSeek-Coder 33B Instruct** model
  - Model size: 18.8GB
  - Optimized for structured data extraction and JSON generation
  - Average inference time: 30-60s per request
  - Configured in `config/settings.py`: `LLM_MODEL_NAME = "deepseek-coder:33b-instruct"`
- Neo4j and Qdrant use default local settings

### LLM Client
All agents use the centralized `core/llm_client.py` which provides:
- **Timeout handling**: 120s default (configurable per agent)
- **Retry logic**: 3 attempts with exponential backoff
- **JSON validation**: Automatic parsing and validation of JSON responses
- **Error handling**: Graceful degradation with detailed error messages

## API Usage

Upload and process transcript:
```bash
curl -X POST "http://localhost:8000/upload_transcript/" \
  -F "file=@/path/to/transcript.txt"
```

## Key Dependencies
- `langgraph`: Multi-agent orchestration
- `langchain`: LLM integration framework
- `sentence-transformers`: Text embeddings (all-MiniLM-L6-v2)
- `fastapi`/`uvicorn`: API framework
- `sqlalchemy`: ORM for PostgreSQL
- `qdrant-client`, `neo4j`: Vector and graph database clients