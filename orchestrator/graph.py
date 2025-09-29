from config.settings import settings
from orchestrator.state import AgentState
from langgraph.graph import StateGraph

# Import agents
from agents.parser.parser_agent import ParserAgent
from agents.structuring.structuring_agent import StructuringAgent
from agents.chunker.chunker import ChunkerAgent
from agents.extractor.extractor import ExtractorAgent
from agents.email.email_agent import EmailAgent
from agents.social.social_agent import SocialAgent
from agents.sales_coach.sales_coach_agent import SalesCoachAgent
from agents.crm.crm_agent import CRMAgent  # Now sequential!
from agents.persistence.persistence_agent import PersistenceAgent
from agents.historian.historian_agent import HistorianAgent

# Initialize agents
parser_agent = ParserAgent(settings)
structuring_agent = StructuringAgent(settings)
chunker_agent = ChunkerAgent(settings)
extractor_agent = ExtractorAgent(settings)
email_agent = EmailAgent(settings)
social_agent = SocialAgent(settings)
sales_coach_agent = SalesCoachAgent(settings)
crm_agent = CRMAgent(settings)  # Enhanced CRM
persistence_agent = PersistenceAgent(settings)
historian_agent = HistorianAgent(settings)

# --- OPTIMIZED NODE DEFINITIONS ---

async def parser_node(state: AgentState):
    """Parse raw transcript into structured dialogue"""
    structured_dialogue = await parser_agent.run(file_path=state.get("file_path"))
    return {"structured_dialogue": structured_dialogue}

async def structuring_node(state: AgentState):
    """Analyze conversation phases and structure"""
    structured_dialogue = state.get("structured_dialogue")
    conversation_phases = await structuring_agent.run(structured_dialogue=structured_dialogue)
    return {"conversation_phases": conversation_phases}

async def chunker_node(state: AgentState):
    """Segment content for optimal processing"""
    file_path = state.get("file_path")
    chunks = await chunker_agent.run(file_path=file_path)
    return {"chunks": chunks}

async def extractor_node(state: AgentState):
    """Extract key insights and data"""
    chunks = state.get("chunks")
    extracted_data = await extractor_agent.run(chunks=chunks)
    return {"extracted_data": extracted_data}

# --- PARALLEL SPECIALIZED PROCESSING ---

async def email_node(state: AgentState):
    """Generate follow-up email drafts and next steps"""
    extracted_data = state.get("extracted_data")
    email_draft = await email_agent.run(extracted_data=extracted_data)
    return {"email_draft": email_draft}

async def social_node(state: AgentState):
    """Generate social media content and testimonials"""
    chunks = state.get("chunks")
    social_content = await social_agent.run(chunks=chunks)
    return {"social_content": social_content}

async def sales_coach_node(state: AgentState):
    """Analyze performance and provide coaching feedback"""
    chunks = state.get("chunks")
    coaching_feedback = await sales_coach_agent.run(chunks=chunks)
    return {"coaching_feedback": coaching_feedback}

# --- ENHANCED SEQUENTIAL PROCESSING ---

async def crm_node(state: AgentState):
    """
    CRM AGENT - Now processes ALL upstream data
    
    This is the key optimization: CRM agent now has access to:
    - Original extracted data
    - Generated email content  
    - Social media opportunities
    - Coaching feedback and insights
    
    Creates comprehensive, CRM data for maximum business value.
    """
    print("🏢 CRM Agent: Aggregating ALL processed insights...")
    
    # Gather all processed data
    extracted_data = state.get("extracted_data", {})
    email_draft = state.get("email_draft", {})
    social_content = state.get("social_content", {})
    coaching_feedback = state.get("coaching_feedback", {})
    
    # Enhanced CRM processing with complete context
    crm_data = await crm_agent.run(
        extracted_data=extracted_data,
        email_draft=email_draft,           # NEW: Email follow-up context
        social_opportunities=social_content,   # NEW: Marketing opportunities  
        coaching_insights=coaching_feedback    # NEW: Performance context
    )
    
    return {"crm_data": crm_data}

async def persistence_node(state: AgentState):
    """
    Save all processed data to primary storage (PostgreSQL + Qdrant)
    Now has access to enriched CRM data with complete context
    """
    print("💾 Persistence Agent: Saving enriched data to primary storage...")
    
    db_status = await persistence_agent.run(
        file_path=state.get("file_path"),
        chunks=state.get("chunks"),
        crm_data=state.get("crm_data"),           # Enhanced CRM data
        social_content=state.get("social_content"),
        email_draft=state.get("email_draft"),
        coaching_feedback=state.get("coaching_feedback")  # Additional context
    )
    return {"db_save_status": db_status}

async def historian_node(state: AgentState):
    """
    Build knowledge graph with COMPLETE processed context
    Has access to all agent outputs for maximum relationship building
    """
    print("📜 Historian Agent: Building knowledge graph with complete context...")
    
    # Historian now gets the full picture for maximum relationship value
    historian_status = await historian_agent.run(state=state)
    return {"historian_status": historian_status}

# --- OPTIMIZED WORKFLOW CONSTRUCTION ---

def create_optimized_workflow():
    """
    Creates the optimized workflow for maximum data capture and value
    """
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("parser", parser_node)
    workflow.add_node("structuring", structuring_node)
    workflow.add_node("chunker", chunker_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("email", email_node)
    workflow.add_node("social", social_node)
    workflow.add_node("sales_coach", sales_coach_node)
    workflow.add_node("crm", crm_node)           # Enhanced!
    workflow.add_node("persistence", persistence_node)
    workflow.add_node("historian", historian_node)
    
    # PHASE 1: Sequential preprocessing
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "structuring")
    workflow.add_edge("structuring", "chunker")
    workflow.add_edge("chunker", "extractor")
    
    # PHASE 2: Parallel specialized processing
    workflow.add_edge("extractor", "email")
    workflow.add_edge("extractor", "social")
    workflow.add_edge("extractor", "sales_coach")
    
    # PHASE 3: Sequential data aggregation and enrichment
    workflow.add_edge("email", "crm")         # CRM gets email insights
    workflow.add_edge("social", "crm")        # CRM gets social opportunities
    workflow.add_edge("sales_coach", "crm")   # CRM gets coaching insights
    
    # PHASE 4: Sequential storage with complete context
    workflow.add_edge("crm", "persistence")   # Save enriched data
    workflow.add_edge("persistence", "historian")  # Build complete knowledge graph
    
    workflow.set_finish_point("historian")
    
    return workflow

# Create the optimized workflow
app = create_optimized_workflow().compile()