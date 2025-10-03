<!-- markdownlint-disable MD022 MD032 MD030 MD007 MD031 MD046 MD001 MD025 MD050 MD009 MD024 MD047 MD041 -->
stellar-sales-system/
│
├── PLAYBOOK/                  # [NEW] The master instructional manual for the project.
│   ├── 00_Project_Overview.md
│   ├── 01_Project_Structure.md
│   └── SPRINT_01_...md
│
├── agents/                    # Core directory for all specialized AI agents.
│   ├── base_agent.py          # Abstract base class for all agents.
│   ├── chunker/
│   │   └── chunker.py
│   ├── crm/
│   │   └── crm_agent.py
│   ├── email/
│   │   └── email_agent.py
│   ├── embedder/              # [NEW] Houses the new EmbedderAgent.
│   │   └── embedder_agent.py
│   ├── extractor/
│   │   └── extractor.py
│   ├── historian/
│   │   └── historian_agent.py
│   ├── knowledge_analyst/     # [NEW] Houses the new KnowledgeAnalystAgent.
│   │   └── knowledge_analyst_agent.py
│   ├── parser/
│   │   └── parser_agent.py
│   ├── persistence/
│   │   └── persistence_agent.py
│   ├── sales_coach/
│   │   └── sales_coach_agent.py
│   ├── sales_copilot/         # Will be significantly upgraded.
│   │   └── sales_copilot_agent.py
│   ├── social/
│   │   └── social_agent.py
│   └── structuring/
│       └── structuring_agent.py
│
├── api/                       # FastAPI application for API endpoints.
│   └── app.py
│
├── config/                    # Configuration management.
│   └── settings.py            # Pydantic settings, loaded from .env.
│
├── core/                      # Core application logic and database interactions.
│   └── database/
│       ├── models.py          # SQLAlchemy models for PostgreSQL.
│       ├── neo4j.py           # Neo4j connection manager.
│       ├── postgres.py        # PostgreSQL connection manager.
│       └── qdrant.py          # Qdrant connection manager.
│
├── data/                      # Data storage for transcripts.
│   └── transcripts/
│
├── orchestrator/              # LangGraph workflow definition.
│   ├── graph.py               # The main StateGraph connecting all agents.
│   ├── pipeline.py            # Entry point to run the graph.
│   └── state.py               # Definition of the AgentState TypedDict.
│
├── scripts/                   # Utility and testing scripts.
│   ├── ask_copilot.py         # CLI to interact with the Sales Copilot.
│   └── ...
│
├── .gitignore
├── docker-compose.yml         # Defines and configures all services (DBs, Ollama).
├── Makefile                   # Convenience commands for installation, Docker, etc.
└── requirements.txt           # Python package dependencies.