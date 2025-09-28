# Stellar Sales System

## 🚀 Overview

Stellar Sales System is an advanced multi-agent sales intelligence platform that transforms sales conversations into actionable insights. Built with LangGraph and powered by specialized AI agents, it processes sales transcripts through a sophisticated pipeline to extract customer data, generate follow-up content, and provide coaching feedback.

### Key Features

- **Multi-Agent Architecture**: 10 specialized agents working in orchestrated harmony
- **Intelligent Processing**: LLM-powered analysis for deep conversation insights
- **Multi-Database Persistence**: PostgreSQL for structured data, Neo4j for knowledge graphs, Qdrant for semantic search
- **Automated Content Generation**: Email drafts, social media posts, and CRM-ready data
- **Sales Coaching**: AI-powered performance analysis and improvement suggestions
- **RESTful API**: Easy integration with existing sales workflows

## 🏗️ Architecture

### System Design

The system employs a directed acyclic graph (DAG) workflow orchestrated by LangGraph:

```
Transcript → Parser → Structuring → Chunker → Extractor → [Parallel Processing] → Persistence
                                                              ├── CRM Agent
                                                              ├── Email Agent
                                                              ├── Social Agent
                                                              ├── Sales Coach Agent
                                                              └── Historian Agent
```

### Agent Ecosystem

#### Sequential Processing Agents

1. **Parser Agent** (`agents/parser/`)
   - Converts raw transcript files into structured dialogue format
   - Identifies speakers and timestamps
   - Prepares data for downstream processing

2. **Structuring Agent** (`agents/structuring/`)
   - Analyzes conversation flow and phases
   - Identifies key moments and transitions
   - Creates hierarchical conversation structure

3. **Chunker Agent** (`agents/chunker/`)
   - Intelligently segments conversations into processable chunks
   - Maintains context while optimizing for LLM token limits
   - Preserves semantic coherence across chunks

4. **Extractor Agent** (`agents/extractor/`)
   - Leverages LLM to extract key information
   - Identifies customer needs, objections, and action items
   - Generates structured data from unstructured text

#### Parallel Processing Agents

5. **CRM Agent** (`agents/crm/`)
   - Formats extracted data for CRM integration
   - Standardizes customer information
   - Creates opportunity and lead records

6. **Email Agent** (`agents/email/`)
   - Generates personalized follow-up email drafts
   - Incorporates conversation highlights and next steps
   - Maintains appropriate tone and context

7. **Social Agent** (`agents/social/`)
   - Creates social media content from conversation insights
   - Generates testimonials and success stories
   - Identifies shareable moments

8. **Sales Coach Agent** (`agents/sales_coach/`)
   - Analyzes sales representative performance
   - Provides actionable coaching feedback
   - Identifies areas for improvement

9. **Historian Agent** (`agents/historian/`)
   - Updates Neo4j knowledge graph with conversation history
   - Builds relationship networks
   - Tracks objection patterns and resolutions

10. **Persistence Agent** (`agents/persistence/`)
    - Manages final data storage across all databases
    - Ensures data consistency and integrity
    - Handles vector embeddings for semantic search

## 💾 Database Architecture

### PostgreSQL (Relational Data)
- **Purpose**: Primary data storage for structured information
- **Contents**: Transcripts, extracted data, generated content
- **Schema**: Defined in `core/database/models.py`

### Neo4j (Knowledge Graph)
- **Purpose**: Relationship mapping and pattern analysis
- **Contents**: Customer relationships, meeting history, objection patterns
- **Access**: Bolt protocol on port 7687
- **Browser UI**: http://localhost:7474

### Qdrant (Vector Database)
- **Purpose**: Semantic search and similarity matching
- **Contents**: Transcript embeddings for intelligent retrieval
- **Model**: Sentence-Transformers (all-MiniLM-L6-v2)
- **Dashboard**: http://localhost:6333/dashboard

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- 8GB RAM minimum (for running all services)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/stellar-sales-system.git
   cd stellar-sales-system
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Start Docker services**
   ```bash
   make docker-up
   ```

5. **Initialize databases**
   ```bash
   ./venv/bin/python scripts/init_db.py
   ```

6. **Run the API server**
   ```bash
   make run-api
   ```

## 📡 API Usage

### Upload and Process Transcript

```bash
curl -X POST "http://localhost:8000/upload_transcript/" \
  -F "file=@/path/to/transcript.txt"
```

### Response Format

```json
{
  "status": "success",
  "filename": "transcript.txt",
  "message": "File uploaded and processed successfully.",
  "results": {
    "transcript_id": 22,
    "crm_data": {...},
    "email_draft": "...",
    "social_content": {...},
    "coaching_feedback": {...}
  }
}
```

## 🧪 Testing

### Test Database Connections
```bash
./venv/bin/python scripts/test_db.py
```

### Run Neo4j Diagnostics
```bash
./venv/bin/python diagnose_neo4j.py
```

### Test Individual Agents
```bash
./venv/bin/python -m pytest tests/agents/
```

## 🔧 Development

### Project Structure

```
stellar-sales-system/
├── orchestrator/       # Workflow orchestration
├── agents/            # Specialized AI agents
├── core/              # Core infrastructure
├── api/               # REST API endpoints
├── config/            # Configuration management
├── scripts/           # Utility scripts
└── data/              # Data storage
```

### Adding New Agents

1. Create agent module in `agents/` directory
2. Inherit from `BaseAgent` class
3. Implement `async run()` method
4. Register in `orchestrator/graph.py`
5. Update `AgentState` in `orchestrator/state.py`

### Common Commands

```bash
# Start all services
make docker-up

# Stop all services
make docker-down

# View service logs
docker logs stellar_postgres
docker logs stellar_neo4j
docker logs stellar_qdrant
docker logs stellar_ollama

# Access service UIs
# Neo4j Browser: http://localhost:7474
# Qdrant Dashboard: http://localhost:6333/dashboard
# API Docs: http://localhost:8000/docs
```

## 🔐 Configuration

### Environment Variables

Key settings in `.env`:

```bash
# PostgreSQL
POSTGRES_DB=stellar_sales
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Neo4j
NEO4J_PASSWORD=password

# LLM
LLM_MODEL_NAME=mistral

# Embeddings
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### Advanced Settings

Configure in `config/settings.py`:
- Database connection pools
- Timeout values
- Model parameters
- File paths

## 📊 Performance & Scaling

### Resource Requirements

- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Storage**: 20GB for models and data

### Optimization Tips

1. **Batch Processing**: Process multiple transcripts concurrently
2. **Model Selection**: Use smaller models for faster processing
3. **Database Indexing**: Ensure proper indexes on frequently queried fields
4. **Connection Pooling**: Adjust pool sizes based on load

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/stellar-sales-system/issues)
- Documentation: See [CLAUDE.md](CLAUDE.md) for AI assistant guidance
- Email: support@stellarsales.example.com

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web API framework
- [Neo4j](https://neo4j.com/) - Graph database
- [Qdrant](https://qdrant.tech/) - Vector database
- [Ollama](https://ollama.ai/) - Local LLM deployment

---

**Stellar Sales System** - Transforming conversations into revenue 🚀