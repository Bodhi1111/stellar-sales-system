# Enhanced KnowledgeAnalystAgent with RAG-based extraction + Hybrid Search

import json
from typing import List, Dict, Any
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from agents.base_agent import BaseAgent
from config.settings import Settings
from core.database.neo4j import neo4j_manager
from core.llm_client import LLMClient
from core.hybrid_search import HybridSearchEngine


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

        # Initialize embedder model for semantic search (same as EmbedderAgent uses)
        from sentence_transformers import SentenceTransformer
        self.embedder_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

        # Initialize hybrid search engine (BM25 + Vector)
        self.hybrid_search = HybridSearchEngine(
            k1=1.5,  # BM25 term frequency saturation
            b=0.75,  # BM25 length normalization
            rrf_k=60  # RRF constant
        )

    async def _extract_header_only(self, transcript_id: str) -> Dict[str, Any]:
        """
        Fast fallback: Extract only from header chunk (no LLM, just parsing).
        Used when CRM data not available yet.
        """
        try:
            # Get header chunk (index 0)
            results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id)),
                        FieldCondition(key="chunk_index", match=MatchValue(value=0))
                    ]
                ),
                limit=1,
                with_payload=True
            )

            if not results[0]:
                return self._empty_entities()

            header_text = results[0][0].payload.get("text", "")
            lines = [line.strip() for line in header_text.split('\n') if line.strip()]

            # Parse header structure (same as parser)
            return {
                "client_name": lines[1] if len(lines) > 1 else "",
                "client_email": lines[2] if len(lines) > 2 else "",
                "meeting_date": lines[3] if len(lines) > 3 else "",
                "transcript_id": lines[4] if len(lines) > 4 else transcript_id,
                "marital_status": None,
                "children_count": 0,
                "meeting_outcome": None,
                "objections_raised": [],
                "products_discussed": ["Estate Planning"]
            }
        except Exception as e:
            print(f"   ⚠️ Header extraction failed: {e}")
            return self._empty_entities()

    def _empty_entities(self) -> Dict[str, Any]:
        """Return empty entity structure"""
        return {
            "client_name": "",
            "client_email": "",
            "meeting_date": "",
            "transcript_id": "",
            "marital_status": None,
            "children_count": 0,
            "meeting_outcome": None,
            "objections_raised": [],
            "products_discussed": []
        }

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

        # Optimized prompt with header extraction instructions
        prompt = f"""TASK: Extract sales data from transcript excerpt

INSTRUCTIONS:
1. Read the transcript excerpt carefully
2. If this is the HEADER section (has blank lines separating fields), extract ALL metadata:

   HEADER STRUCTURE (blank lines between fields):
   - Non-blank line 1: Meeting title
   - Non-blank line 2: Client full name (REQUIRED)
   - Non-blank line 3: Client email address (REQUIRED)
   - Non-blank line 4: Meeting date ISO 8601 format (REQUIRED - YYYY-MM-DDTHH:MM:SSZ)
   - Non-blank line 5: Transcript ID numeric value (REQUIRED)
   - Non-blank line 6: Meeting URL
   - Non-blank line 7: Duration in decimal minutes

   Example header:
   Sylvia Flynn: Estate Planning Advisor Meeting

   Sylvia Flynn

   sylviapf@aol.com

   2025-10-07T17:00:00Z

   61965940

   https://fathom.video/calls/432760777

   80.13395555000001

3. For dialogue sections (timestamped HH:MM:SS - Speaker), extract ONLY facts explicitly stated
4. Use bullet points for each fact found
5. If a field is not mentioned, skip it

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

        for i, result in enumerate(results):
            # Handle exceptions returned by asyncio.gather(return_exceptions=True)
            if isinstance(result, Exception):
                failed_chunks.append(i + 1)
                print(f"      ❌ Chunk {i+1} exception: {result}")
                continue

            # Normal case: unpack the tuple
            index, response, success = result
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

    async def _retrieve_with_hybrid_search(self, transcript_id: str, top_k: int = 15) -> List[str]:
        """
        HYBRID SEARCH: BM25 keyword search + Vector semantic search with RRF fusion.

        Strategy:
        1. Fetch all chunks for this transcript from Qdrant
        2. Index chunks in BM25 for keyword search
        3. For each query:
           - Run BM25 keyword search
           - Run vector semantic search
           - Fuse results with RRF (Reciprocal Rank Fusion)
        4. Deduplicate and return top_k chunks

        Expected improvement: 50% → 75-85% extraction accuracy
        """
        print(f"   🔍🔤 HYBRID SEARCH: Retrieving chunks for transcript {transcript_id}...")

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # STEP 1: Fetch ALL chunks for this transcript
            all_chunks_results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
                ),
                limit=100,  # Fetch all chunks (assuming <100 per transcript)
                with_payload=True
            )

            all_chunks = all_chunks_results[0]
            if not all_chunks:
                print(f"      ⚠️ No chunks found for transcript {transcript_id}")
                return []

            print(f"      📚 Loaded {len(all_chunks)} chunks from Qdrant")

            # STEP 2: Sort chunks by chunk_index to maintain consistent ordering
            # CRITICAL: BM25 array index MUST match Qdrant chunk_index for correct retrieval
            all_chunks_sorted = sorted(all_chunks, key=lambda x: x.payload.get('chunk_index', 0))
            chunk_payloads = [c.payload for c in all_chunks_sorted]
            self.hybrid_search.index_chunks(chunk_payloads)

            # STEP 3: Multi-query hybrid retrieval
            queries = [
                "client name email address phone contact information",
                "estate value assets real estate property house LLC business worth",
                "deal price cost deposit payment money dollars fee",
                "next steps follow-up action items schedule timeline",
                "marital status married single spouse children family daughter son grandchildren",
                "location state city Washington California address where lives",
                "meeting date when today appointment scheduled",
                "objections concerns hesitation worried not sure"
            ]

            hybrid_chunk_indices = set()

            for query in queries:
                # Vector search
                query_vector = self.embedder_model.encode(query, show_progress_bar=False).tolist()
                vector_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=Filter(
                        must=[FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))]
                    ),
                    limit=10,
                    with_payload=True,
                    score_threshold=0.15  # Lower threshold for hybrid
                )

                # Convert to (chunk_index, score) format
                vector_results_formatted = [
                    (r.payload["chunk_index"], r.score)
                    for r in vector_results
                ]

                # Hybrid search with RRF fusion
                fused_indices = self.hybrid_search.hybrid_search(
                    query=query,
                    vector_results=vector_results_formatted,
                    top_k=5,
                    bm25_weight=0.4,  # 40% keyword matching
                    vector_weight=0.6  # 60% semantic matching
                )

                hybrid_chunk_indices.update(fused_indices)

            # STEP 4: Ensure header chunk (index 0) is always included
            # Header contains critical metadata: name, email, transcript_id, date
            hybrid_chunk_indices.add(0)

            # STEP 5: Retrieve full text for selected chunks
            final_chunks = []
            for chunk_idx in sorted(hybrid_chunk_indices)[:top_k]:
                chunk_data = self.hybrid_search.get_chunk_by_index(chunk_idx)
                if chunk_data:
                    final_chunks.append(chunk_data["text"])

            header_included = 0 in hybrid_chunk_indices
            print(f"      ✅ Retrieved {len(final_chunks)} chunks via HYBRID SEARCH (BM25 + Vector + RRF)")
            if header_included:
                print(f"         (1 header + {len(final_chunks)-1} dialogue chunks)")

            return final_chunks

        except Exception as e:
            print(f"      ❌ Hybrid search failed: {e}, falling back to vector-only")
            return await self._retrieve_relevant_chunks(transcript_id, top_k)

    async def _retrieve_relevant_chunks(self, transcript_id: str, top_k: int = 15) -> List[str]:
        """
        FALLBACK: Vector-only retrieval (used if hybrid search fails).

        Strategy:
        1. Extract header chunk first (contains transcript_id, name, email, date)
        2. Use multi-query semantic retrieval for different data aspects
        3. Filter by critical conversation phases
        4. Deduplicate and return top_k most relevant chunks
        """
        print(f"   🔍 Retrieving chunks from Qdrant for transcript {transcript_id}...")

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

            all_retrieved_chunks = []
            chunk_ids = set()  # Track chunk indices to avoid duplicates

            # STEP 1: Get the header chunk (always chunk_index=0, contains critical metadata)
            header_results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id)),
                        FieldCondition(key="chunk_index", match=MatchValue(value=0))
                    ]
                ),
                limit=1,
                with_payload=True
            )

            if header_results[0]:
                header_chunk = header_results[0][0].payload
                all_retrieved_chunks.append(header_chunk["text"])
                chunk_ids.add(header_chunk["chunk_index"])
                print(f"      ✅ Retrieved header chunk (contains: name, email, date, transcript_id)")

            # STEP 2: Multi-query semantic retrieval for different data aspects
            # Each query targets specific fields we need to extract
            queries = [
                "client name, full name, email address, phone number, contact information",
                "estate value, total worth, assets, real estate properties, house value, LLC business",
                "deal price, total cost, service price, deposit amount, payment, money, dollars",
                "next steps, follow-up, action items, schedule, timeline, what happens next",
                "marital status, married, single, spouse name, children count, family structure",
                "location, state, city, address, where client lives, Washington, California",  # NEW: Location query
                "meeting date, when meeting happened, date of meeting, today's date",  # NEW: Date query
                "grandchildren, daughter, family members, heirs, beneficiaries"  # NEW: Family structure
            ]

            # Critical conversation phases that typically contain the data we need
            critical_phases = [
                "client's estate details",
                "closing",
                "collecting money",
                "price negotiation",
                "scheduling client meeting",
                "client's goals"
            ]

            chunks_per_query = 4  # INCREASED: Retrieve 4 chunks per query aspect (was 2)

            for query in queries:
                # Generate query embedding
                query_vector = self.embedder_model.encode(query, show_progress_bar=False).tolist()

                # Search with semantic similarity
                # Note: conversation_phase filtering is optional (won't exclude chunks without it)
                search_results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=Filter(
                        must=[
                            FieldCondition(key="transcript_id", match=MatchValue(value=transcript_id))
                        ]
                    ),
                    limit=chunks_per_query,
                    with_payload=True,
                    score_threshold=0.2  # LOWERED: 0.2 threshold for better coverage (was 0.3)
                )

                # Add unique chunks
                for result in search_results:
                    chunk_idx = result.payload["chunk_index"]
                    if chunk_idx not in chunk_ids:
                        all_retrieved_chunks.append(result.payload["text"])
                        chunk_ids.add(chunk_idx)

            # Limit to top_k chunks (header + semantically retrieved)
            final_chunks = all_retrieved_chunks[:top_k]

            print(f"      ✅ Retrieved {len(final_chunks)} chunks via semantic search + metadata filtering")
            print(f"         (1 header + {len(final_chunks)-1} semantically matched)")
            return final_chunks

        except Exception as e:
            print(f"      ❌ ERROR retrieving from Qdrant: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to simple scroll if semantic search fails
            print(f"      ⚠️ Falling back to simple scroll retrieval...")
            try:
                results = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter={"must": [{"key": "transcript_id", "match": {"value": transcript_id}}]},
                    limit=top_k,
                    with_payload=True
                )
                chunks = [point.payload["text"] for point in results[0]]
                print(f"      ✅ Fallback retrieved {len(chunks)} chunks")
                return chunks
            except Exception as fallback_error:
                print(f"      ❌ Fallback also failed: {fallback_error}")
                return []

    async def run(self, transcript_id: str, file_path: Path, chunks: List[Dict] = None, header_metadata: Dict = None, crm_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        OPTIMIZED: Build Neo4j knowledge graph using CRM data (no extraction bottleneck).

        Previous architecture extracted entities here (44s bottleneck!).
        New architecture: CRM Agent does comprehensive extraction, we just build graph.
        """
        print(f"📊 KnowledgeAnalystAgent: Building knowledge graph for {file_path.name}...")

        # Use CRM data if available (passed from workflow after CRM runs)
        # Otherwise create minimal extracted_entities for backward compatibility
        if crm_data:
            print("   ✅ Using CRM data for knowledge graph")
            extracted_entities = {
                "client_name": crm_data.get("client_name"),
                "client_email": crm_data.get("client_email"),
                "marital_status": crm_data.get("marital_status"),
                "children_count": crm_data.get("children_count", 0),
                "meeting_outcome": crm_data.get("outcome"),
                "objections_raised": crm_data.get("objections_raised", "").split("; ") if crm_data.get("objections_raised") else [],
                "products_discussed": [crm_data.get("product_discussed", "Estate Planning")],
            }
        else:
            # NEW: Override with header metadata if available
            if header_metadata:
                print("   ✅ Using header metadata for knowledge graph")
                extracted_entities = {
                    'meeting_title': header_metadata.get('meeting_title') or "",
                    'client_name': header_metadata.get('client_name') or "",
                    'client_email': header_metadata.get('client_email') or "",
                    'meeting_date': header_metadata.get('meeting_date') or "",
                    'transcript_id': header_metadata.get('transcript_id') or transcript_id,
                    'marital_status': None,
                    'children_count': 0,
                    'meeting_outcome': None,
                    'objections_raised': [],
                    'products_discussed': ["Estate Planning"]
                }
            else:
                # Fallback: extract minimal data from header (very fast - no LLM calls!)
                print("   ⚠️ No header metadata available, extracting header only (fast)")
                extracted_entities = await self._extract_header_only(transcript_id)

        print(f"   -> Entities for graph: {json.dumps(extracted_entities, indent=2)}")

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
