from langgraph.graph import StateGraph, END
from typing import Dict, Any

from orchestrator.state import AgentState
from config.settings import settings

# --- Import ALL agents for the Intelligence First workflow ---
# Foundational Agents
from agents.parser.parser_agent import ParserAgent
from agents.structuring.structuring_agent import StructuringAgent
from agents.chunker.chunker import ChunkerAgent

# Intelligence Core Agents
from agents.embedder.embedder_agent import EmbedderAgent
from agents.knowledge_analyst.knowledge_analyst_agent import KnowledgeAnalystAgent

# Legacy Downstream Agents (for compatibility)
from agents.email.email_agent import EmailAgent
from agents.social.social_agent import SocialAgent
from agents.sales_coach.sales_coach_agent import SalesCoachAgent
from agents.crm.crm_agent import CRMAgent

# Persistence Agent
from agents.persistence.persistence_agent import PersistenceAgent

# --- Initialize ALL agents ---
parser_agent = ParserAgent(settings)
structuring_agent = StructuringAgent(settings)
chunker_agent = ChunkerAgent(settings)
embedder_agent = EmbedderAgent(settings)
knowledge_analyst_agent = KnowledgeAnalystAgent(settings)
email_agent = EmailAgent(settings)
social_agent = SocialAgent(settings)
sales_coach_agent = SalesCoachAgent(settings)
crm_agent = CRMAgent(settings)
persistence_agent = PersistenceAgent(settings)

# --- Define Agent Nodes for the Intelligence First Workflow ---

async def parser_node(state: AgentState) -> Dict[str, Any]:
    """Parse raw transcript and extract transcript_id from header"""
    result = await parser_agent.run(file_path=state["file_path"])
    return {
        "structured_dialogue": result["structured_dialogue"],
        "transcript_id": result["transcript_id"]
    }

async def structuring_node(state: AgentState) -> Dict[str, Any]:
    """Analyze conversation phases and structure"""
    conversation_phases = await structuring_agent.run(structured_dialogue=state["structured_dialogue"])
    return {"conversation_phases": conversation_phases}

async def chunker_node(state: AgentState) -> Dict[str, Any]:
    """Segment content for optimal processing"""
    chunks = await chunker_agent.run(file_path=state["file_path"])
    return {"chunks": chunks}

async def knowledge_analyst_node(state: AgentState) -> Dict[str, Any]:
    """Extract entities and build knowledge graph"""
    result = await knowledge_analyst_agent.run(chunks=state["chunks"], file_path=state["file_path"])
    # Populate both new and legacy fields for compatibility
    return {
        "extracted_entities": result.get("extracted_entities"),
        "extracted_data": result.get("extracted_entities")  # For backward compatibility
    }

async def embedder_node(state: AgentState) -> Dict[str, Any]:
    """Generate and store embeddings in Qdrant"""
    if not state.get("transcript_id"):
        print("   - Halting embedder: missing transcript_id.")
        return {}
    await embedder_agent.run(chunks=state["chunks"], transcript_id=state["transcript_id"])
    return {}

# --- Legacy Downstream Nodes ---
async def email_node(state: AgentState) -> Dict[str, Any]:
    """Generate follow-up email drafts"""
    email_draft = await email_agent.run(extracted_data=state["extracted_data"])
    return {"email_draft": email_draft}

async def social_node(state: AgentState) -> Dict[str, Any]:
    """Generate social media content"""
    social_content = await social_agent.run(chunks=state["chunks"])
    return {"social_content": social_content}

async def sales_coach_node(state: AgentState) -> Dict[str, Any]:
    """Provide coaching feedback"""
    coaching_feedback = await sales_coach_agent.run(chunks=state["chunks"])
    return {"coaching_feedback": coaching_feedback}

async def crm_node(state: AgentState) -> Dict[str, Any]:
    """Aggregate all insights for CRM"""
    crm_data = await crm_agent.run(
        extracted_data=state["extracted_data"],
        chunks=state["chunks"],
        email_draft=state.get("email_draft"),
        social_opportunities=state.get("social_content"),
        coaching_insights=state.get("coaching_feedback")
    )
    return {"crm_data": crm_data}

async def persistence_node(state: AgentState) -> Dict[str, Any]:
    """Save all data to PostgreSQL"""
    await persistence_agent.run(
        file_path=state["file_path"],
        chunks=state["chunks"],
        crm_data=state["crm_data"],
        social_content=state["social_content"],
        email_draft=state["email_draft"],
        coaching_feedback=state.get("coaching_feedback"),
        transcript_id=state["transcript_id"]  # Use external_id from header
    )
    return {"db_save_status": {"status": "success"}}

# --- Master Workflow Construction ---
def create_master_workflow():
    """
    Creates the Intelligence First workflow:
    1. Parse and extract transcript_id from header
    2. Structure conversation
    3. Chunk text
    4. Parallel: Build knowledge graph + Create embeddings
    5. Legacy downstream agents for backward compatibility
    6. Persist everything at the end
    """
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("structuring", structuring_node)
    workflow.add_node("chunker", chunker_node)
    workflow.add_node("knowledge_analyst", knowledge_analyst_node)
    workflow.add_node("embedder", embedder_node)
    workflow.add_node("email", email_node)
    workflow.add_node("social", social_node)
    workflow.add_node("sales_coach", sales_coach_node)
    workflow.add_node("crm", crm_node)
    workflow.add_node("persistence", persistence_node)

    # --- Define the Graph Edges ---
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "structuring")
    workflow.add_edge("structuring", "chunker")

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
    workflow.add_edge(["embedder", "crm"], "persistence")

    workflow.add_edge("persistence", END)

    return workflow.compile()

app = create_master_workflow()