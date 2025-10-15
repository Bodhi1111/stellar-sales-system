import json
import re
from typing import List, Dict, Any, Optional

from agents.base_agent import BaseAgent
from config.settings import Settings
# REMOVED: Neo4j integration (not used in current pipeline)
# from core.database.neo4j import neo4j_manager
from core.qdrant_rag_mixin import QdrantRAGMixin


class SalesCopilotAgent(BaseAgent, QdrantRAGMixin):
    """
    Acts as a powerful "Librarian" tool for the reasoning engine. It queries
    the knowledge base (Qdrant) to answer specific questions posed by the Planner.

    Uses QdrantRAGMixin for parent-child retrieval with hybrid search.

    Note: Neo4j graph search disabled in current pipeline (Qdrant-only mode).
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._init_qdrant_rag(settings)  # Initialize RAG capabilities
        # REMOVED: self.neo4j_manager = neo4j_manager

    async def _search_qdrant(
        self,
        query: str,
        transcript_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Performs semantic search using parent-child retrieval pattern.

        Args:
            query: Search query
            transcript_id: Optional transcript to scope search to
            limit: Max results to return

        Returns:
            List of chunk payloads with text and metadata
        """
        try:
            print(f"   - SalesCopilot: Searching Qdrant for '{query}'")
            if transcript_id:
                print(f"     Scoped to transcript: {transcript_id}")

            # Use RAG mixin for parent-child retrieval
            # If no transcript_id, search the most recent transcript
            if not transcript_id:
                # Get all available transcript IDs and use the most recent
                from qdrant_client.models import ScrollRequest
                scroll_result = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=1,
                    with_payload=True
                )
                if scroll_result[0]:
                    transcript_id = scroll_result[0][0].payload.get("transcript_id", "")
                    print(f"     Auto-selected transcript: {transcript_id}")
                else:
                    print(f"     ⚠️ No transcripts found in Qdrant")
                    return []

            chunks = await self.retrieve_chunks(
                transcript_id=transcript_id,
                queries=[query],
                top_k=limit,
                use_hybrid=True
            )

            # Convert chunk texts to payload format for compatibility
            results = [{"text": chunk, "source": "qdrant"} for chunk in chunks]

            print(f"     ✅ Retrieved {len(results)} chunks")
            return results

        except Exception as e:
            print(f"     ❌ Qdrant search failed: {e}")
            import traceback
            traceback.print_exc()
            return [{"error": f"Qdrant search failed: {str(e)}"}]

    async def _search_neo4j(self, query: str, params: Dict = None) -> List[Dict]:
        """DISABLED: Neo4j graph search (graceful degradation to Qdrant-only)"""
        print(f"   - ⚠️ Neo4j search disabled, using Qdrant fallback")
        return [{"error": "Neo4j disabled in current pipeline"}]

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
        transcript_id = data.get("transcript_id")  # Optional transcript context

        print(f"🤖 SalesCopilotTool activated with query: '{query}'")

        try:
            if "objection" in query.lower() and "client" in query.lower():
                print("   - Strategy: Multi-step (Neo4j -> Qdrant)")
                client_name = self._extract_client_name(query)
                if not client_name:
                    return {"error": "Could not determine client name from query."}

                objections = await self._search_neo4j(
                    "MATCH (c:Client)-[:PARTICIPATED_IN]->(m)-[:CONTAINED]->(o:Objection) WHERE c.name =~ $client_name RETURN o.text as objection LIMIT 1",
                    # Case-insensitive regex
                    {"client_name": f"(?i){client_name}"}
                )

                if objections and "error" not in objections[0]:
                    objection_text = objections[0]['objection']
                    vector_results = await self._search_qdrant(
                        query=objection_text,
                        transcript_id=transcript_id
                    )
                    results = {"strategy": "multi_step",
                               "graph_results": objections, "vector_results": vector_results}
                else:
                    results = {
                        "error": f"No objections found for client '{client_name}'."}
            else:
                print("   - Strategy: Simple Vector Search (Qdrant)")
                vector_results = await self._search_qdrant(
                    query=query,
                    transcript_id=transcript_id
                )
                results = {"strategy": "vector_search",
                           "results": vector_results}

            return {"response": results}

        except Exception as e:
            print(f"   ❌ ERROR in SalesCopilotAgent: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Agent execution failed: {str(e)}", "results": []}
