# Enhanced KnowledgeAnalystAgent with RAG-based extraction

import json
from typing import List, Dict, Any
from pathlib import Path
from qdrant_client import QdrantClient

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.database.neo4j import neo4j_manager
from core.llm_client import LLMClient


class KnowledgeAnalystAgent(BaseAgent):
    """
    Analyzes transcript chunks using a Map-Reduce strategy to extract
    a comprehensive set of entities for the Neo4j knowledge graph.

    Optimized for DeepSeek-Coder 33B model with:
    - Structured JSON schema outputs
    - Step-by-step reasoning instructions
    - Robust timeout and retry handling
    """

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.llm_client = LLMClient(settings, timeout=180, max_retries=2)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "transcripts"

    def _get_required_fields_prompt(self) -> str:
        """
        Returns a formatted string of the required fields for the LLM prompt.
        This uses the highly specific list you provided.
        """
        return """
        - "transcript_id": a unique identifier for the meeting
        - "meeting_date": when the meeting occurred
        - "client_name": the customer's full name
        - "spouse_name": the customer's spouse's name, if mentioned
        - "client_email": the customer's email address
        - "client_phone_number": the customer's phone number, if mentioned
        - "client_state": the customer's state of residence
        - "marital_status": "Single", "Married", "Divorced", "Widowed", or "Separated"
        - "children_count": the number of children
        - "estate_value": the total estimated estate worth in dollars
        - "real_estate_count": the number of properties owned
        - "real_estate_locations": states of properties owned, if mentioned
        - "llc_interest": any business interests or LLCs mentioned
        - "deal": the total service cost
        - "deposit": the deposit amount paid
        - "product_discussed": a list of products like "Estate Planning" or "Life Insurance"
        - "objections_raised": a list of client concerns and objections
        - "meeting_outcome": "Won", "Lost", "Pending", or "Follow-up Scheduled"
        - "next_steps": a list of action items
        """

    async def _process_single_chunk(self, chunk: str, index: int, total: int) -> tuple:
        """Process a single chunk and return (index, result, success)"""
        print(f"   -> Mapping chunk {index+1}/{total} to facts...")

        # Optimized prompt for DeepSeek-Coder with step-by-step instructions
        prompt = f"""TASK: Extract sales data from transcript excerpt

INSTRUCTIONS:
1. Read the transcript excerpt carefully
2. Extract ONLY facts that are explicitly stated (no inference)
3. Use bullet points for each fact found
4. If a field is not mentioned, skip it

REQUIRED FIELDS:
{self._get_required_fields_prompt()}

TRANSCRIPT EXCERPT:
---
{chunk}
---

EXTRACTED FACTS (bullet points):
"""

        result = self.llm_client.generate(
            prompt=prompt,
            format_json=False,
            timeout=90  # 90s timeout per chunk
        )

        if result["success"]:
            print(f"      ✅ Chunk {index+1} processed in {result['elapsed_time']:.1f}s")
            return (index, result["response"], True)
        else:
            print(f"      ❌ Chunk {index+1} failed: {result['error']}")
            return (index, result['error'], False)

    async def _map_chunks_to_facts(self, chunks: List[str]) -> str:
        """
        MAP STEP: Analyzes each chunk individually to extract raw facts.
        Uses parallel processing for faster execution with local LLM.
        """
        import asyncio

        print(f"   🚀 Processing {len(chunks)} chunks in parallel...")

        # Create tasks for all chunks
        tasks = [
            self._process_single_chunk(chunk, i, len(chunks))
            for i, chunk in enumerate(chunks)
        ]

        # Process all chunks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results and track failures
        all_facts = []
        failed_chunks = []

        for index, response, success in results:
            if isinstance(response, Exception):
                failed_chunks.append(index + 1)
                print(f"      ❌ Chunk {index+1} exception: {response}")
            elif success:
                all_facts.append(response)
            else:
                failed_chunks.append(index + 1)

        if failed_chunks:
            print(f"   ⚠️ Failed to process chunks: {failed_chunks}")

        return "\n".join(all_facts)

    async def _reduce_facts_to_json(self, all_facts: str) -> Dict[str, Any]:
        """
        REDUCE STEP: Synthesizes aggregated facts into a single JSON object.
        Uses DeepSeek-Coder's JSON generation capabilities with schema definition.
        """
        print("   -> Reducing all extracted facts into a final JSON object...")

        # Optimized prompt with explicit JSON schema for DeepSeek-Coder
        prompt = f"""TASK: Consolidate extracted facts into structured JSON

INSTRUCTIONS:
1. Read all the extracted facts below
2. Merge and consolidate duplicate information
3. Output ONLY valid JSON with the exact schema provided
4. Use null for missing strings, [] for missing arrays, 0 for missing numbers

JSON SCHEMA:
{{
  "transcript_id": "string or null",
  "meeting_date": "string or null",
  "client_name": "string or null",
  "spouse_name": "string or null",
  "client_email": "string or null",
  "client_phone_number": "number or null",
  "client_state": "string or null",
  "marital_status": "string or null",
  "children_count": number or null,
  "estate_value": number or null,
  "real_estate_count": number or null,
  "real_estate_locations": ["array", "of", "strings"],
  "llc_interest": "string or null",
  "deal": number or null,
  "deposit": number or null,
  "products_discussed": ["array", "of", "strings"],
  "objections_raised": ["array", "of", "strings"],
  "meeting_outcome": "string or null",
  "next_steps": ["array", "of", "strings"]
}}
  "real_estate_locations": ["array", "of", "strings"],
  "llc_interest": "number or null",
  "deal": number or null,
  "deposit": number or null,
  "products_discussed": ["array", "of", "strings"],
  "objections_raised": ["array", "of", "strings"],
  "meeting_outcome": "string or null",
  "next_steps": ["array", "of", "strings"]
}}

RAW FACTS:
---
{all_facts}
---

OUTPUT (valid JSON only):
"""

        result = self.llm_client.generate_json(
            prompt=prompt,
            timeout=120  # 2 minute timeout for reduce step
        )

        if result["success"]:
            print(
                f"   ✅ Facts reduced successfully in {result['elapsed_time']:.1f}s")
            return result["data"]
        else:
            print(f"   ❌ Failed to reduce facts: {result['error']}")
            return {}

    async def _retrieve_relevant_chunks(self, transcript_id: str, top_k: int = 15) -> List[str]:
        """
        Retrieve most relevant chunks from Qdrant for the given transcript.
        Uses simple scroll to get all chunks for this transcript_id.
        """
        print(f"   🔍 Retrieving chunks from Qdrant for transcript {transcript_id}...")

        try:
            # Scroll through all points for this transcript
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {"key": "transcript_id", "match": {"value": transcript_id}}
                    ]
                },
                limit=top_k,
                with_payload=True
            )

            chunks = [point.payload["text"] for point in results[0]]
            print(f"      ✅ Retrieved {len(chunks)} chunks from Qdrant")
            return chunks

        except Exception as e:
            print(f"      ❌ ERROR retrieving from Qdrant: {e}")
            return []

    async def run(self, transcript_id: str, file_path: Path) -> Dict[str, Any]:
        """
        NEW RAG-BASED APPROACH: Query Qdrant for chunks, then extract entities.
        This eliminates the LLM map phase bottleneck.
        """
        print(f"📊 KnowledgeAnalystAgent: Analyzing transcript for {file_path.name}...")

        # Retrieve chunks from Qdrant (already embedded and stored)
        chunks = await self._retrieve_relevant_chunks(transcript_id, top_k=15)

        if not chunks:
            print("   - No chunks found in Qdrant, skipping analysis.")
            return {"knowledge_graph_status": "skipped", "extracted_entities": {}}

        # Now do a single-pass extraction (no map phase, just reduce)
        extracted_facts = await self._map_chunks_to_facts(chunks)
        if not extracted_facts:
            print("   - No facts extracted, skipping analysis.")
            return {"knowledge_graph_status": "skipped", "extracted_entities": {}}

        extracted_entities = await self._reduce_facts_to_json(extracted_facts)
        print(
            f"   -> Final extracted entities: {json.dumps(extracted_entities, indent=2)}")

        try:
            client_name = extracted_entities.get("client_name")
            if not client_name or "unknown" in client_name.lower():
                print("   - Skipping Neo4j update: Client name not found.")
                return {"knowledge_graph_status": "skipped", "extracted_entities": extracted_entities}

            # --- ENHANCEMENT: Enrich the Client node with more properties ---
            await neo4j_manager.execute_query(
                """
                MERGE (c:Client {name: $client_name})
                SET c.email = $email,
                    c.marital_status = $marital_status,
                    c.children_count = $children_count
                """,
                {
                    "client_name": client_name,
                    "email": extracted_entities.get("client_email"),
                    "marital_status": extracted_entities.get("marital_status"),
                    "children_count": extracted_entities.get("children_count", 0),
                }
            )

            # --- ENHANCEMENT: Add outcome property to the Meeting node ---
            await neo4j_manager.execute_query(
                """
                MERGE (m:Meeting {filename: $filename})
                SET m.outcome = $outcome
                WITH m
                MATCH (c:Client {name: $client_name})
                MERGE (c)-[:PARTICIPATED_IN]->(m)
                """,
                {
                    "filename": file_path.name,
                    "outcome": extracted_entities.get("meeting_outcome"),
                    "client_name": client_name
                }
            )

            # --- ENHANCEMENT: Add Objection nodes ---
            for objection in extracted_entities.get("objections_raised", []):
                await neo4j_manager.execute_query(
                    """
                    MATCH (m:Meeting {filename: $filename})
                    MERGE (o:Objection {text: $objection_text})
                    MERGE (m)-[:CONTAINED]->(o)
                    """,
                    {"filename": file_path.name, "objection_text": objection}
                )

            for product in extracted_entities.get("products_discussed", []):
                await neo4j_manager.execute_query(
                    """
                    MATCH (m:Meeting {filename: $filename})
                    MERGE (p:Product {name: $product_name})
                    MERGE (m)-[:DISCUSSED]->(p)
                    """,
                    {"filename": file_path.name, "product_name": product}
                )

            print(
                f"   ✅ Successfully updated knowledge graph for {file_path.name}.")
            return {
                "knowledge_graph_status": "success",
                "extracted_entities": extracted_entities
            }
        except Exception as e:
            print(f"   ❌ ERROR during Neo4j update: {type(e).__name__}: {e}")
            return {"knowledge_graph_status": "error", "error_message": str(e)}
