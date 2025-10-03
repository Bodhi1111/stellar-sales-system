<!-- markdownlint-disable MD022 MD032 MD030 MD007 MD031 MD046 MD001 MD025 MD050 MD009 MD024 MD047 MD041 -->
# Playbook: The Stellar Sales System

## 1. Project Vision & Scope

### Vision Statement
The Stellar Sales System is an autonomous, self-improving sales intelligence platform designed to transform raw sales meeting transcripts into actionable revenue-generating opportunities and performance insights. It functions as a tireless team of AI agents, each specializing in a core aspect of the post-meeting sales cycle.

### Core Problem Statement
The manual review of sales meeting transcripts is inefficient, inconsistent, and unscalable. Valuable opportunities for follow-ups, marketing content, sales coaching, and long-term relationship building are frequently missed. The knowledge gained in one meeting remains isolated and fails to contribute to the collective intelligence of the sales organization.

### Core Goals
1.  **Automate Intelligence Extraction:** Eliminate manual work by having AI agents process meeting transcripts.
2.  **Generate Client-Facing Assets:** Automatically create high-quality recap emails and identify action items.
3.  **Create Marketing & Lead-Gen Content:** Extract valuable insights and quotes that can be repurposed into social media content.
4.  **Provide Actionable Sales Coaching:** Analyze sales professional performance and offer data-driven feedback.
5.  **Build a Centralized Knowledge Brain:** Create a unified, queryable knowledge base from all meeting data.

## 2. Project State Summary

### Where We Are Now (Current State)
The system is a multi-agent pipeline orchestrated by LangGraph. It processes transcripts through a sequential pre-processing phase (`Parser`, `Structuring`, `Chunker`, `Extractor`) followed by a parallel fan-out to specialist agents (`Email`, `Social`, `SalesCoach`). The results are then aggregated and saved to our databases (PostgreSQL, Qdrant, Neo4j).

### Where We Are Going (The Agentic Reasoning Upgrade)
The next evolution will transform the system into a dynamic, agentic reasoning engine. We will build a deeper Knowledge Core and a new cognitive workflow with agents that can plan, verify information, and synthesize novel insights. The `SalesCopilotAgent` will become the primary interface to this new, more intelligent system.