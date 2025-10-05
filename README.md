# Stellar Sales System

**Multi-Agent Sales Intelligence Platform with Agent-AI and Human-First CRM Integration**

---

## 🚀 Overview

Stellar Sales System is a modular, multi-agent platform for sales workflow automation, powerful analytics, and deep CRM integration. Built with **FastAPI** and **LangGraph**, it processes sales transcripts, extracts actionable insights, and seamlessly syncs intelligent agent outputs with a user-friendly CRM (Baserow).

*Agents generate outputs for CRM, email, social, and coaching. Baserow provides the human interface; Qdrant, Neo4j, and PostgreSQL power the AI backend.*

---

## 🌐 Architecture

- **Data Ingestion**: Transcripts are processed by an orchestrated LangGraph pipeline of specialized agents.
- **Multi-Agent Workflow**:
  - **Sequential Agents**: `ParserAgent → StructuringAgent → ChunkerAgent → ExtractorAgent`
  - **Parallel Agents**: `CRMAgent (CRM data)`, `EmailAgent`, `SocialAgent`, `SalesCoachAgent`, `HistorianAgent`, `PersistenceAgent`
- **Databases**:
  - **PostgreSQL**: Primary data store
  - **Qdrant**: Vector embeddings for semantic/AI search
  - **Neo4j**: Knowledge graph for relationships and reasoning
  - **Baserow**: Human-friendly CRM UI (syncs with PostgreSQL via BaserowManager)

See [CLAUDE.md](./CLAUDE.md) for a full technical workflow.

---

## 🛠️ Quick Start

