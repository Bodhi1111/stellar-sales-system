# This is the new, enhanced code for agents/knowledge_analyst/knowledge_analyst_agent.py

import json
import requests
from typing import List, Dict, Any
from pathlib import Path

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.database.neo4j import neo4j_manager

class KnowledgeAnalystAgent(BaseAgent):
    """
    Analyzes transcript chunks using a Map-Reduce strategy to extract
    a comprehensive set of entities for the Neo4j knowledge graph,
    ensuring no data is lost from long transcripts.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.api_url = settings.OLLAMA_API_URL
        self.model_name = settings.LLM_MODEL_NAME

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

    async def _map_chunks_to_facts(self, chunks: List[str]) -> str:
        """MAP STEP: Analyzes each chunk individually to extract raw facts."""
        all_facts = []
        failed_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"   -> Mapping chunk {i+1}/{len(chunks)} to facts...")
            prompt = f"""
            You are a fact-extraction specialist. Read the following excerpt from a sales transcript and extract any and all potential facts related to the following fields. Do not infer or summarize, just extract raw data points.

            Required Fields of Interest:
            {self._get_required_fields_prompt()}

            Transcript Excerpt:
            ---
            {chunk}
            ---

            Extracted Facts (use bullet points):
            """
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            try:
                response = requests.post(self.api_url, json=payload).json().get("response", "")
                if response:
                    all_facts.append(response)
            except Exception as e:
                failed_chunks.append(i+1)
                print(f"      - Warning: Could not process chunk {i+1}: {e}")

        if failed_chunks:
            print(f"   ⚠️ Failed to process chunks: {failed_chunks}")
        return "\n".join(all_facts)

    async def _reduce_facts_to_json(self, all_facts: str) -> Dict[str, Any]:
        """REDUCE STEP: Synthesizes aggregated facts into a single JSON object."""
        print("   -> Reducing all extracted facts into a final JSON object...")
        prompt = f"""
        You are a data synthesis expert. You will be given a list of raw, unordered facts extracted from a sales transcript. Your job is to analyze all these facts and consolidate them into a single, structured JSON object.

        Use the following fields. If a fact is not present, use a null value, an empty list, or 0 for numeric fields.
        {self._get_required_fields_prompt()}

        List of Raw Facts:
        ---
        {all_facts}
        ---

        Respond ONLY with the final, consolidated JSON object.
        """
        payload = {"model": self.model_name, "prompt": prompt, "format": "json", "stream": False}
        try:
            response_json_str = requests.post(self.api_url, json=payload).json().get("response", "{}")
            return json.loads(response_json_str)
        except Exception as e:
            print(f"      - Error: Could not reduce facts to JSON: {e}")
            return {}

    async def run(self, chunks: List[str], file_path: Path) -> Dict[str, Any]:
        """Analyzes transcript, extracts entities, and saves them to Neo4j."""
        print(f"📊 KnowledgeAnalystAgent: Analyzing transcript for {file_path.name}...")

        extracted_facts = await self._map_chunks_to_facts(chunks)
        if not extracted_facts:
             print("   - No facts extracted, skipping analysis.")
             return {"knowledge_graph_status": "skipped", "extracted_entities": {}}

        extracted_entities = await self._reduce_facts_to_json(extracted_facts)
        print(f"   -> Final extracted entities: {json.dumps(extracted_entities, indent=2)}")

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

            print(f"   ✅ Successfully updated knowledge graph for {file_path.name}.")
            return {
                "knowledge_graph_status": "success",
                "extracted_entities": extracted_entities
            }
        except Exception as e:
            print(f"   ❌ ERROR during Neo4j update: {type(e).__name__}: {e}")
            return {"knowledge_graph_status": "error", "error_message": str(e)}
