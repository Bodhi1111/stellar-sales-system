<!-- markdownlint-disable MD022 MD032 MD030 MD007 MD031 MD046 MD001 MD025 MD050 MD009 MD024 MD047 MD041 -->
# Playbook: SPRINT 01 - Building The Knowledge Core

## Sprint Goal

To lay the foundational "brain" of the Stellar system. By the end of this sprint, our application will have a long-term **semantic memory (Qdrant)** and **relational memory (Neo4j)** that are created automatically and in parallel for every new transcript. This sprint implements the "Intelligence First" architecture.

---

### Epic 1.1: The Semantic Memory Layer

**Objective:** Create a new, specialized agent responsible for converting text into meaning (embeddings) and storing it in our vector database, Qdrant. This agent's sole purpose is to establish the semantic foundation for all future intelligent queries.

#### **Task 1.1.1: Create the `EmbedderAgent`**

* **Rationale:** We are creating a dedicated agent for embeddings to adhere to the Single Responsibility Principle. This agent does one thing and does it perfectly: it creates the vector representation of the transcript chunks. This is a crucial separation of concerns from the `PersistenceAgent`, which handles metadata storage.

* **Step 1: Create the Agent File**
    * In the `agents/` directory, create a new subdirectory named `embedder`.
    * Inside `agents/embedder/`, create a new file named `embedder_agent.py`.

* **Step 2: Add the Code**
    * The following complete code should be placed in `agents/embedder/embedder_agent.py`.

    ```python
# This is the new, enhanced code for agents/embedder/embedder_agent.py

import uuid
from typing import List, Dict, Any
from datetime import datetime # NEW IMPORT
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from agents.base_agent import BaseAgent
from config.settings import Settings

class EmbedderAgent(BaseAgent):
    """
    This agent's sole responsibility is to take raw text chunks, generate
    vector embeddings, and store them in the Qdrant vector database.
    It forms the core of the system's semantic memory.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "transcripts"
        self._ensure_qdrant_collection_exists()

    def _ensure_qdrant_collection_exists(self):
        """Creates the Qdrant collection if it doesn't already exist."""
        try:
            self.qdrant_client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_model.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )

    async def run(self, chunks: List[str], transcript_id: int) -> Dict[str, Any]:
        """
        Generates embeddings for a list of text chunks and upserts them into Qdrant.
        """
        print(f"🧠 EmbedderAgent: Generating {len(chunks)} embeddings for transcript ID {transcript_id}...")

        try:
            embeddings = self.embedding_model.encode(
                chunks, convert_to_tensor=False, show_progress_bar=False
            ).tolist()

            # --- ENHANCEMENT: Add richer metadata to each payload ---
            payloads = [
                {
                    "transcript_id": transcript_id,
                    "chunk_index": i, # NEW
                    "text": chunk,
                    "doc_type": "transcript_chunk",
                    "word_count": len(chunk.split()), # NEW
                    "created_at": datetime.now().isoformat() # NEW
                } for i, chunk in enumerate(chunks)
            ]

            # --- ENHANCEMENT: Use deterministic IDs for idempotency ---
            deterministic_ids = [f"transcript_{transcript_id}_chunk_{i}" for i, _ in enumerate(chunks)]

            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=models.Batch(
                    ids=deterministic_ids, # UPDATED
                    vectors=embeddings,
                    payloads=payloads
                ),
                wait=True
            )

            print(f"   ✅ Successfully saved {len(chunks)} embeddings to Qdrant.")
            return {"embedding_status": "success", "vector_count": len(chunks)}

        except Exception as e:
            # --- ENHANCEMENT: More specific error logging ---
            print(f"   ❌ ERROR in EmbedderAgent: {type(e).__name__}: {e}")
            return {"embedding_status": "error", "error_message": str(e)}

---

### Epic 1.2: The Relational Memory Layer

**Objective:** Create an agent that understands the relationships within the conversation and builds our knowledge graph in Neo4j. This agent runs in parallel to the `EmbedderAgent`.

#### **Task 1.2.1: Create the `KnowledgeAnalystAgent`**

* **Rationale:** A vector database knows what things *mean*, but a knowledge graph knows how they are *connected*. This agent builds the map of "who said what," "which client raised what objection," etc. This is essential for the advanced, multi-step queries our Sales Copilot will perform later.

* **Step 1: Create the Agent File**
    * In the `agents/` directory, create a new subdirectory named `knowledge_analyst`.
    * Inside `agents/knowledge_analyst/`, create a new file named `knowledge_analyst_agent.py`.

* **Step 2: Add the Code**
    * The following complete code should be placed in `agents/knowledge_analyst/knowledge_analyst_agent.py`.

    ```python
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
              You are a fact-extraction specialist. Read the following excerpt 
  from a sales transcript and extract any and all potential facts related to the
   following fields. Do not infer or summarize, just extract raw data points.

              Required Fields of Interest:
              {self._get_required_fields_prompt()}

              Transcript Excerpt:
              ---
              {chunk}
              ---

              Extracted Facts (use bullet points):
              """
              payload = {"model": self.model_name, "prompt": prompt, "stream": 
  False}
              try:
                  response = requests.post(self.api_url, 
  json=payload).json().get("response", "")
                  if response:
                      all_facts.append(response)
              except Exception as e:
                  failed_chunks.append(i+1)
                  print(f"      - Warning: Could not process chunk {i+1}: {e}")
          
          if failed_chunks:
              print(f"   ⚠️ Failed to process chunks: {failed_chunks}")
          return "\n".join(all_facts)

      async def _reduce_facts_to_json(self, all_facts: str) -> Dict[str, Any]:
          """REDUCE STEP: Synthesizes aggregated facts into a single JSON 
  object."""
          print("   -> Reducing all extracted facts into a final JSON 
  object...")
          prompt = f"""
          You are a data synthesis expert. You will be given a list of raw, 
  unordered facts extracted from a sales transcript. Your job is to analyze all 
  these facts and consolidate them into a single, structured JSON object.

          Use the following fields. If a fact is not present, use a null value, 
  an empty list, or 0 for numeric fields.
          {self._get_required_fields_prompt()}

          List of Raw Facts:
          ---
          {all_facts}
          ---

          Respond ONLY with the final, consolidated JSON object.
          """
          payload = {"model": self.model_name, "prompt": prompt, "format": 
  "json", "stream": False}
          try:
              response_json_str = requests.post(self.api_url, 
  json=payload).json().get("response", "{}")
              return json.loads(response_json_str)
          except Exception as e:
              print(f"      - Error: Could not reduce facts to JSON: {e}")
              return {}

      async def run(self, chunks: List[str], file_path: Path) -> Dict[str, Any]:
          """Analyzes transcript, extracts entities, and saves them to Neo4j."""
          print(f"📊 KnowledgeAnalystAgent: Analyzing transcript for 
  {file_path.name}...")

          extracted_facts = await self._map_chunks_to_facts(chunks)
          if not extracted_facts:
               print("   - No facts extracted, skipping analysis.")
               return {"knowledge_graph_status": "skipped", 
  "extracted_entities": {}}
          
          extracted_entities = await self._reduce_facts_to_json(extracted_facts)
          print(f"   -> Final extracted entities: 
  {json.dumps(extracted_entities, indent=2)}")

          try:
              client_name = extracted_entities.get("client_name")
              if not client_name or "unknown" in client_name.lower():
                  print("   - Skipping Neo4j update: Client name not found.")
                  return {"knowledge_graph_status": "skipped", 
  "extracted_entities": extracted_entities}

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
                      "marital_status": 
  extracted_entities.get("marital_status"),
                      "children_count": extracted_entities.get("children_count",
   0),
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

              print(f"   ✅ Successfully updated knowledge graph for 
  {file_path.name}.")
              return {
                  "knowledge_graph_status": "success",
                  "extracted_entities": extracted_entities
              }
          except Exception as e:
              print(f"   ❌ ERROR during Neo4j update: {type(e).__name__}: {e}")
              return {"knowledge_graph_status": "error", "error_message": str(e)}"

---

### Epic 1.3: Integrating the Knowledge Core into the Main Workflow

**Objective:** To rewire the central orchestrator to use our new "Intelligence First" agents. This is where we bring the new semantic and relational memory online, making it the foundation for all downstream processing.

#### **Task 1.3.1: Update the `AgentState`**

* **Rationale:** Our `AgentState` is the data "basket" that gets passed between nodes in our graph. We need to add fields to carry the new information generated by our `KnowledgeAnalystAgent` and to track the `transcript_id` which is essential for linking our vector embeddings back to our relational database.
* **File to Modify:** `orchestrator/state.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/state.py`.

    ```python
from typing import TypedDict, List, Dict, Any, Optional
from pathlib import Path

class AgentState(TypedDict):
    """
    This is the basket that carries our data through the graph.
    It is updated to support the new "Intelligence First" architecture
    while maintaining backward compatibility for existing agents.
    """
    # --- Initial Input ---
    file_path: Path
    
    # --- Preprocessing Outputs ---
    raw_text: str
    structured_dialogue: List[Dict[str, Any]]
    conversation_phases: List[Dict[str, Any]]
    chunks: List[str] # Now a simple list of strings

    # --- Intelligence Core Outputs ---
    transcript_id: Optional[int] # PostgreSQL ID for linking all data
    extracted_entities: Dict[str, Any] # NEW: From KnowledgeAnalystAgent

    # --- Backward Compatibility & Legacy Fields ---
    extracted_data: Dict[str, Any] # PRESERVED: For backward compatibility with existing agents like CRMAgent.
    crm_data: Dict[str, Any]
    email_draft: str
    social_content: Dict[str, Any]
    coaching_feedback: Dict[str, Any]

    # --- Persistence Agent Outputs ---
    db_save_status: Dict[str, Any]
    historian_status: Dict[str, Any] # FIX: Corrected syntax, removed extra bracket

#### **Task 1.3.2: Re-Architect the Orchestrator Graph**

* **Rationale:** This is the culmination of Sprint 1. We are replacing the old, linear graph with our new "Intelligence First" architecture. This new graph correctly incorporates the `StructuringAgent`, solves the `transcript_id` dependency by using an initial persistence step, and efficiently creates the semantic and relational knowledge in parallel. It also maintains backward compatibility for the legacy downstream agents by populating the `extracted_data` field they expect.
* **File to Modify:** `orchestrator/graph.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/graph.py`.

    ```python
    from langgraph.graph import StateGraph, END
    from typing import Dict, Any

    from orchestrator.state import AgentState
    from config.settings import settings

    # --- Import ALL agents for the new ingestion workflow ---
    # Foundational Agents
    from agents.parser.parser_agent import ParserAgent
    from agents.structuring.structuring_agent import StructuringAgent
    from agents.chunker.chunker import ChunkerAgent

    # Intelligence Core Agents
    from agents.persistence.initial_persistence_agent import InitialPersistenceAgent
    from agents.embedder.embedder_agent import EmbedderAgent
    from agents.knowledge_analyst.knowledge_analyst_agent import KnowledgeAnalystAgent

    # Legacy Downstream Agents (for compatibility)
    from agents.email.email_agent import EmailAgent
    from agents.social.social_agent import SocialAgent
    from agents.sales_coach.sales_coach_agent import SalesCoachAgent
    from agents.crm.crm_agent import CRMAgent

    # Final Persistence Agent
    from agents.persistence.final_persistence_agent import FinalPersistenceAgent

    # --- Initialize ALL agents ---
    parser_agent = ParserAgent(settings)
    structuring_agent = StructuringAgent(settings)
    initial_persistence_agent = InitialPersistenceAgent(settings)
    chunker_agent = ChunkerAgent(settings)
    embedder_agent = EmbedderAgent(settings)
    knowledge_analyst_agent = KnowledgeAnalystAgent(settings)
    email_agent = EmailAgent(settings)
    social_agent = SocialAgent(settings)
    sales_coach_agent = SalesCoachAgent(settings)
    crm_agent = CRMAgent(settings)
    final_persistence_agent = FinalPersistenceAgent(settings)

    # --- Define Agent Nodes for the Ingestion Workflow ---

    async def parser_node(state: AgentState) -> Dict[str, Any]:
        structured_dialogue = await parser_agent.run(file_path=state["file_path"])
        return {"structured_dialogue": structured_dialogue}

    async def structuring_node(state: AgentState) -> Dict[str, Any]:
        conversation_phases = await structuring_agent.run(structured_dialogue=state["structured_dialogue"])
        return {"conversation_phases": conversation_phases}

    async def initial_persistence_node(state: AgentState) -> Dict[str, Any]:
        result = await initial_persistence_agent.run(file_path=state["file_path"])
        return {"transcript_id": result["transcript_id"]}

    async def chunker_node(state: AgentState) -> Dict[str, Any]:
        chunks = await chunker_agent.run(file_path=state["file_path"])
        return {"chunks": chunks}

    async def knowledge_analyst_node(state: AgentState) -> Dict[str, Any]:
        result = await knowledge_analyst_agent.run(chunks=state["chunks"], file_path=state["file_path"])
        # Populate both new and legacy fields for compatibility
        return {
            "extracted_entities": result.get("extracted_entities"),
            "extracted_data": result.get("extracted_entities") # For backward compatibility
        }

    async def embedder_node(state: AgentState) -> Dict[str, Any]:
        if not state.get("transcript_id"):
            print("   - Halting embedder: missing transcript_id.")
            return {}
        await embedder_agent.run(chunks=state["chunks"], transcript_id=state["transcript_id"])
        return {}

    # --- Legacy Downstream Nodes ---
    async def email_node(state: AgentState) -> Dict[str, Any]:
        email_draft = await email_agent.run(extracted_data=state["extracted_data"])
        return {"email_draft": email_draft}

    async def social_node(state: AgentState) -> Dict[str, Any]:
        social_content = await social_agent.run(chunks=state["chunks"])
        return {"social_content": social_content}
        
    async def sales_coach_node(state: AgentState) -> Dict[str, Any]:
        coaching_feedback = await sales_coach_agent.run(chunks=state["chunks"])
        return {"coaching_feedback": coaching_feedback}

    async def crm_node(state: AgentState) -> Dict[str, Any]:
        crm_data = await crm_agent.run(
            extracted_data=state["extracted_data"],
            chunks=state["chunks"],
            email_draft=state.get("email_draft"),
            social_opportunities=state.get("social_content"),
            coaching_insights=state.get("coaching_feedback")
        )
        return {"crm_data": crm_data}

    async def final_persistence_node(state: AgentState) -> Dict[str, Any]:
        await final_persistence_agent.run(state)
        return {"db_save_status": {"status": "success"}}

    # --- Master Workflow Construction ---
    def create_master_workflow():
        workflow = StateGraph(AgentState)

        # Add all nodes
        workflow.add_node("parser", parser_node)
        workflow.add_node("structuring", structuring_node)
        workflow.add_node("initial_persistence", initial_persistence_node)
        workflow.add_node("chunker", chunker_node)
        workflow.add_node("knowledge_analyst", knowledge_analyst_node)
        workflow.add_node("embedder", embedder_node)
        workflow.add_node("email", email_node)
        workflow.add_node("social", social_node)
        workflow.add_node("sales_coach", sales_coach_node)
        workflow.add_node("crm", crm_node)
        workflow.add_node("final_persistence", final_persistence_node)

        # --- Define the Graph Edges ---
        workflow.set_entry_point("parser")
        workflow.add_edge("parser", "structuring")
        workflow.add_edge("structuring", "initial_persistence")
        workflow.add_edge("initial_persistence", "chunker")

        # After chunking, fan out to the two parallel intelligence core agents
        workflow.add_edge("chunker", "knowledge_analyst")
        workflow.add_edge("chunker", "embedder")

        # After the knowledge analyst runs, fan out to the legacy downstream agents
        workflow.add_edge("knowledge_analyst", "email")
        workflow.add_edge("knowledge_analyst", "social")
        workflow.add_edge("knowledge_analyst", "sales_coach")

        # Converge legacy agents into the CRM agent
        workflow.add_edge(["email", "social", "sales_coach"], "crm")

        # This is the final join: all work must be complete before the final save.
        # This includes the parallel embedder and the entire CRM branch.
        workflow.add_edge(["embedder", "crm"], "final_persistence")
        
        workflow.add_edge("final_persistence", END)

        return workflow.compile()

    app = create_master_workflow()

    ```

    **Architect's Note:** As you can see from the `embedder_node` placeholder, we've uncovered a critical dependency: the `EmbedderAgent` needs the `transcript_id` from PostgreSQL, but the `PersistenceAgent` (which creates that ID) currently runs at the end of the pipeline. This is a classic workflow challenge that our new architecture must solve. We will address this head-on in the next Sprint when we refactor the persistence logic. For now, we have correctly identified the problem and defined the necessary components.

---