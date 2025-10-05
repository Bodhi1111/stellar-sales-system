import json
import re
from typing import List, Dict, Any

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.database.qdrant import qdrant_manager
from core.database.neo4j import neo4j_manager
from qdrant_client import models


class SalesCopilotAgent(BaseAgent):
    """
    Acts as a powerful "Librarian" tool for the reasoning engine. It can
    query the unified knowledge base (Qdrant and Neo4j) to answer specific
    questions posed by the Planner.
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.qdrant_manager = qdrant_manager
        self.neo4j_manager = neo4j_manager

    async def _search_qdrant(self, query: str, doc_type: str, limit: int = 3) -> List[Dict]:
        """Performs a targeted, filtered semantic search in Qdrant."""
        try:
            print(f"   - SalesCopilot: Searching Qdrant for '{query}' with doc_type '{doc_type}'...")
            qdrant_filter = models.Filter(
                must=[models.FieldCondition(key="doc_type", match=models.MatchValue(value=doc_type))]
            )
            search_results = self.qdrant_manager.search(query=query, limit=limit, filter=qdrant_filter)
            return [result.payload for result in search_results]
        except Exception as e:
            return [{"error": f"Qdrant search failed: {str(e)}"}]

    async def _search_neo4j(self, query: str, params: Dict = None) -> List[Dict]:
        """Executes a read query against the Neo4j knowledge graph."""
        try:
            print(f"   - SalesCopilot: Querying Neo4j...")
            return await self.neo4j_manager.execute_read_query(query, params or {})
        except Exception as e:
            return [{"error": f"Neo4j query failed: {str(e)}"}]

    def _extract_client_name(self, query: str) -> str:
        """Simple regex to extract a client name from a query."""
        match = re.search(r"client\s+([\w\s]+)", query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    async def run(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Entry point when the agent is called as a 'tool'."""
        if not data or "query" not in data:
            return {"error": "Missing query in data", "results": []}

        query = data["query"]
        print(f"🤖 SalesCopilotTool activated with query: '{query}'")

        try:
            if "objection" in query.lower() and "client" in query.lower():
                print("   - Strategy: Multi-step (Neo4j -> Qdrant)")
                client_name = self._extract_client_name(query)
                if not client_name:
                    return {"error": "Could not determine client name from query."}

                objections = await self._search_neo4j(
                    "MATCH (c:Client)-[:PARTICIPATED_IN]->(m)-[:CONTAINED]->(o:Objection) WHERE c.name =~ $client_name RETURN o.text as objection LIMIT 1",
                    {"client_name": f"(?i){client_name}"}  # Case-insensitive regex
                )

                if objections and "error" not in objections[0]:
                    objection_text = objections[0]['objection']
                    vector_results = await self._search_qdrant(query=objection_text, doc_type="transcript_chunk")
                    results = {"strategy": "multi_step", "graph_results": objections, "vector_results": vector_results}
                else:
                    results = {"error": f"No objections found for client '{client_name}'."}
            else:
                print("   - Strategy: Simple Vector Search (Qdrant)")
                # Default to searching transcript chunks if not specified
                doc_type = "transcript_chunk"
                if "email" in query.lower():
                    doc_type = "email_draft"  # Simple routing based on keywords

                vector_results = await self._search_qdrant(query=query, doc_type=doc_type)
                results = {"strategy": "vector_search", "results": vector_results}

            return {"response": results}

        except Exception as e:
            print(f"   ❌ ERROR in SalesCopilotAgent: {e}")
            return {"error": f"Agent execution failed: {str(e)}", "results": []}
