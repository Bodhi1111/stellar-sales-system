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
    import uuid
    from typing import List, Dict, Any
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

                payloads = [
                    {
                        "transcript_id": transcript_id,
                        "text": chunk,
                        "doc_type": "transcript_chunk"
                    } for chunk in chunks
                ]

                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=models.Batch(
                        ids=[str(uuid.uuid4()) for _ in chunks],
                        vectors=embeddings,
                        payloads=payloads
                    ),
                    wait=True
                )

                print(f"   ✅ Successfully saved {len(chunks)} embeddings to Qdrant.")
                return {"embedding_status": "success", "vector_count": len(chunks)}

            except Exception as e:
                print(f"   ❌ ERROR in EmbedderAgent: {e}")
                return {"embedding_status": "error", "error_message": str(e)}
    ```

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
    import json
    import requests
    from typing import List, Dict, Any
    from pathlib import Path

    from agents.base_agent import BaseAgent
    from config.settings import Settings
    from core.database.neo4j import neo4j_manager

    class KnowledgeAnalystAgent(BaseAgent):
        """
        Analyzes the transcript to extract key entities (Client, Objections,
        Products, etc.) and their relationships, then populates the Neo4j
        knowledge graph. Forms the relational memory of the system.
        """
        def __init__(self, settings: Settings):
            super().__init__(settings)
            self.api_url = settings.OLLAMA_API_URL
            self.model_name = settings.LLM_MODEL_NAME

        def _construct_prompt(self, full_transcript: str) -> str:
            """Constructs the prompt for the LLM to extract structured entities."""
            prompt = f"""
            You are an expert financial analyst specializing in estate planning.
            Your task is to read the following sales meeting transcript and extract
            key entities and relationships.

            Transcript:
            ---
            {full_transcript}
            ---

            Based ONLY on the transcript, extract the following information.
            If a piece of information is not present, use "Not found".
            - client_name: The full name of the primary client.
            - main_objection: The single biggest concern or objection raised by the client.
            - products_discussed: A list of specific products or services mentioned (e.g., "Revocable Living Trust", "Will Preparation").
            - action_items: A list of concrete next steps or tasks to be completed.

            Respond ONLY with a valid JSON object. Example:
            {{
              "client_name": "Jane Doe",
              "main_objection": "The cost of setting up the trust seems high.",
              "products_discussed": ["Revocable Living Trust", "Power of Attorney"],
              "action_items": ["Schedule follow-up meeting for next week", "Send client the information packet."]
            }}
            """
            return prompt

        async def run(self, chunks: List[str], file_path: Path) -> Dict[str, Any]:
            """
            Analyzes transcript chunks, extracts entities via an LLM, and saves
            them to the Neo4j knowledge graph.
            """
            print(f"📈 KnowledgeAnalystAgent: Analyzing transcript for {file_path.name}...")
            full_transcript = "\\n".join(chunks)
            prompt = self._construct_prompt(full_transcript)
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }

            try:
                # 1. Extract Entities using LLM
                response = requests.post(self.api_url, json=payload)
                response.raise_for_status()
                extracted_entities = json.loads(response.json().get("response", "{}"))
                print(f"   -> LLM extracted entities: {extracted_entities}")

                client_name = extracted_entities.get("client_name", "Unknown Client")
                main_objection = extracted_entities.get("main_objection")

                # 2. Populate Knowledge Graph
                # MERGE the Meeting and Client nodes
                await neo4j_manager.execute_query(
                    \"\"\"
                    MERGE (m:Meeting {{filename: $filename}})
                    MERGE (c:Client {{name: $client_name}})
                    MERGE (c)-[:PARTICIPATED_IN]->(m)
                    \"\"\",
                    {"filename": file_path.name, "client_name": client_name}
                )

                # If an objection was found, MERGE it and connect it
                if main_objection and "not found" not in main_objection.lower():
                    await neo4j_manager.execute_query(
                        \"\"\"
                        MATCH (m:Meeting {{filename: $filename}})
                        MERGE (o:Objection {{text: $objection_text}})
                        MERGE (m)-[:CONTAINED]->(o)
                        \"\"\",
                        {"filename": file_path.name, "objection_text": main_objection}
                    )

                print(f"   ✅ Successfully updated knowledge graph for {file_path.name}.")
                # Pass on the extracted entities for use by other agents
                return {
                    "knowledge_graph_status": "success",
                    "extracted_entities": extracted_entities
                }

            except Exception as e:
                print(f"   ❌ ERROR in KnowledgeAnalystAgent: {e}")
                return {"knowledge_graph_status": "error", "error_message": str(e)}

    ```

---

### Epic 1.3: Integrating the Knowledge Core into the Main Workflow

**Objective:** To rewire the central orchestrator to use our new "Intelligence First" agents. This is where we bring the new semantic and relational memory online, making it the foundation for all downstream processing.

#### **Task 1.3.1: Update the `AgentState`**

* **Rationale:** Our `AgentState` is the data "basket" that gets passed between nodes in our graph. We need to add fields to carry the new information generated by our `KnowledgeAnalystAgent` and to track the `transcript_id` which is essential for linking our vector embeddings back to our relational database.
* **File to Modify:** `orchestrator/state.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/state.py`.

    ```python
    from typing import TypedDict, List, Dict, Any
    from pathlib import Path

    class AgentState(TypedDict):
        """
        This is the basket that carries our data through the graph.
        It is being updated to support the new "Intelligence First" architecture.
        """
        # --- Initial Input & Preprocessing ---
        file_path: Path
        raw_text: str
        structured_dialogue: List[Dict[str, Any]]
        conversation_phases: List[Dict[str, Any]]
        chunks: List[str] # Now a simple list of strings

        # --- Intelligence Core Outputs ---
        transcript_id: int # NEW: PostgreSQL ID for linking data
        extracted_entities: Dict[str, Any] # NEW: From KnowledgeAnalystAgent

        # --- Parallel Agent Outputs ---
        crm_data: Dict[str, Any]
        email_draft: str
        social_content: Dict[str, Any]
        coaching_feedback: Dict[str, Any]

        # --- Persistence Agent Outputs ---
        db_save_status: Dict[str, Any]
        historian_status: Dict[str, Any]
    ```

#### **Task 1.3.2: Re-Architect the Orchestrator Graph**

* **Rationale:** This is the most critical step of Sprint 1. We are fundamentally changing the data flow from a simple linear process to a parallel "Intelligence First" workflow. After the initial parsing, we will immediately create our semantic (Qdrant) and relational (Neo4j) knowledge in parallel. This ensures all downstream agents have access to this rich, multi-modal context.
* **File to Modify:** `orchestrator/graph.py`
* **Step 1: Add the Code**
    * The following complete code should replace the existing content of `orchestrator/graph.py`. This is a significant refactor.

    ```python
    from config.settings import settings
    from orchestrator.state import AgentState
    from langgraph.graph import StateGraph, END
    from typing import Dict, Any

    # --- Import ALL agents, including our new ones ---
    from agents.parser.parser_agent import ParserAgent
    from agents.structuring.structuring_agent import StructuringAgent
    from agents.chunker.chunker import ChunkerAgent
    from agents.embedder.embedder_agent import EmbedderAgent # NEW
    from agents.knowledge_analyst.knowledge_analyst_agent import KnowledgeAnalystAgent # NEW
    from agents.email.email_agent import EmailAgent
    from agents.social.social_agent import SocialAgent
    from agents.sales_coach.sales_coach_agent import SalesCoachAgent
    from agents.crm.crm_agent import CRMAgent
    from agents.persistence.persistence_agent import PersistenceAgent # Will be modified later
    from agents.historian.historian_agent import HistorianAgent

    # --- Initialize ALL agents ---
    parser_agent = ParserAgent(settings)
    structuring_agent = StructuringAgent(settings)
    chunker_agent = ChunkerAgent(settings)
    embedder_agent = EmbedderAgent(settings) # NEW
    knowledge_analyst_agent = KnowledgeAnalystAgent(settings) # NEW
    email_agent = EmailAgent(settings)
    social_agent = SocialAgent(settings)
    sales_coach_agent = SalesCoachAgent(settings)
    crm_agent = CRMAgent(settings)
    persistence_agent = PersistenceAgent(settings) # Will be modified in a later sprint
    historian_agent = HistorianAgent(settings)

    # --- Define Agent Nodes ---

    # --- Phase 1: Sequential Preprocessing ---
    async def parser_node(state: AgentState) -> Dict[str, Any]:
        structured_dialogue = await parser_agent.run(file_path=state["file_path"])
        return {"structured_dialogue": structured_dialogue}

    async def structuring_node(state: AgentState) -> Dict[str, Any]:
        conversation_phases = await structuring_agent.run(structured_dialogue=state["structured_dialogue"])
        return {"conversation_phases": conversation_phases}

    async def chunker_node(state: AgentState) -> Dict[str, Any]:
        chunks = await chunker_agent.run(file_path=state["file_path"])
        return {"chunks": chunks}

    # --- Phase 2: Parallel Intelligence Core (The NEW Architecture) ---
    async def embedder_node(state: AgentState) -> Dict[str, Any]:
        # NOTE: This node will require the `transcript_id` from the persistence step.
        # We will adjust the graph flow later to handle this dependency.
        # For now, we define the node's logic.
        # This highlights a dependency we'll need to solve.
        pass # Placeholder for now

    async def knowledge_analyst_node(state: AgentState) -> Dict[str, Any]:
        result = await knowledge_analyst_agent.run(chunks=state["chunks"], file_path=state["file_path"])
        return {"extracted_entities": result.get("extracted_entities")}

    # --- Phase 3: Downstream Intelligent Agents ---
    # These will be upgraded in a future sprint to use the new knowledge core.
    # For now, their definitions remain the same.
    async def email_node(state: AgentState) -> Dict[str, Any]:
        # Temporarily using old 'extractor' logic for compatibility
        from agents.extractor.extractor import ExtractorAgent
        temp_extractor = ExtractorAgent(settings)
        extracted_data = await temp_extractor.run(chunks=state["chunks"])
        email_draft = await email_agent.run(extracted_data=extracted_data)
        return {"email_draft": email_draft}

    # ... other agent nodes (social, sales_coach, crm, persistence, historian) remain the same for now ...

    # --- Workflow Construction ---
    def create_workflow():
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("parser", parser_node)
        workflow.add_node("structuring", structuring_node)
        workflow.add_node("chunker", chunker_node)
        workflow.add_node("knowledge_analyst", knowledge_analyst_node)
        workflow.add_node("email", email_node) # Example downstream agent

        # Define edges
        workflow.set_entry_point("parser")
        workflow.add_edge("parser", "structuring")
        workflow.add_edge("structuring", "chunker")

        # After chunking, fan out to the knowledge analyst
        workflow.add_edge("chunker", "knowledge_analyst")

        # After analysis, fan out to downstream agents
        workflow.add_edge("knowledge_analyst", "email")

        # ... other edges will be added ...

        workflow.add_edge("email", END) # End for now

        return workflow.compile()

    app = create_workflow()
    ```

    **Architect's Note:** As you can see from the `embedder_node` placeholder, we've uncovered a critical dependency: the `EmbedderAgent` needs the `transcript_id` from PostgreSQL, but the `PersistenceAgent` (which creates that ID) currently runs at the end of the pipeline. This is a classic workflow challenge that our new architecture must solve. We will address this head-on in the next Sprint when we refactor the persistence logic. For now, we have correctly identified the problem and defined the necessary components.

---