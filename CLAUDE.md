# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stellar Sales System is a multi-agent sales intelligence platform built with FastAPI and LangGraph. It processes sales transcripts through a sophisticated pipeline of specialized agents, extracting insights and generating actionable outputs for CRM integration, email drafts, social content, and coaching feedback.

## Architecture

### Core Pipeline Flow
The system uses LangGraph to orchestrate a multi-agent workflow defined in `orchestrator/graph.py`:

1. **Sequential Processing Phase**:
   - ParserAgent → StructuringAgent → ChunkerAgent → ExtractorAgent

2. **Parallel Processing Phase** (Fan-out from ExtractorAgent):
   - CRMAgent - Extracts CRM-ready data
   - EmailAgent - Generates follow-up email drafts
   - SocialAgent - Creates social media content
   - SalesCoachAgent - Provides coaching feedback
   - HistorianAgent - Tracks conversation history
   - PersistenceAgent - Handles database operations

3. **Convergence Phase**:
   - All agents converge back to PersistenceAgent for final data persistence

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
- LLM configuration defaults to Ollama with Mistral model
- Neo4j and Qdrant use default local settings

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