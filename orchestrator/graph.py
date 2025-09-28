from config.settings import settings
from orchestrator.state import AgentState
from langgraph.graph import StateGraph

# Import all our agents
from agents.parser.parser_agent import ParserAgent
from agents.structuring.structuring_agent import StructuringAgent
from agents.chunker.chunker import ChunkerAgent
from agents.extractor.extractor import ExtractorAgent
from agents.crm.crm_agent import CRMAgent
from agents.email.email_agent import EmailAgent
from agents.social.social_agent import SocialAgent
from agents.sales_coach.sales_coach_agent import SalesCoachAgent
from agents.historian.historian_agent import HistorianAgent
from agents.persistence.persistence_agent import PersistenceAgent

# Initialize all our agents
parser_agent = ParserAgent(settings)
structuring_agent = StructuringAgent(settings)
chunker_agent = ChunkerAgent(settings)
extractor_agent = ExtractorAgent(settings)
crm_agent = CRMAgent(settings)
email_agent = EmailAgent(settings)
social_agent = SocialAgent(settings)
sales_coach_agent = SalesCoachAgent(settings)
historian_agent = HistorianAgent(settings)
persistence_agent = PersistenceAgent(settings)

# --- Define Agent Nodes ---
async def parser_node(state: AgentState):
    structured_dialogue = await parser_agent.run(file_path=state.get("file_path"))
    return {"structured_dialogue": structured_dialogue}

async def structuring_node(state: AgentState):
    structured_dialogue = state.get("structured_dialogue")
    conversation_phases = await structuring_agent.run(structured_dialogue=structured_dialogue)
    return {"conversation_phases": conversation_phases}

async def chunker_node(state: AgentState):
    file_path = state.get("file_path")
    chunks = await chunker_agent.run(file_path=file_path)
    return {"chunks": chunks}

async def extractor_node(state: AgentState):
    chunks = state.get("chunks")
    extracted_data = await extractor_agent.run(chunks=chunks)
    return {"extracted_data": extracted_data}

async def crm_node(state: AgentState):
    extracted_data = state.get("extracted_data")
    crm_data = await crm_agent.run(extracted_data=extracted_data)
    return {"crm_data": crm_data}

async def email_node(state: AgentState):
    extracted_data = state.get("extracted_data")
    email_draft = await email_agent.run(extracted_data=extracted_data)
    return {"email_draft": email_draft}

async def social_node(state: AgentState):
    chunks = state.get("chunks")
    social_content = await social_agent.run(chunks=chunks)
    return {"social_content": social_content}

async def sales_coach_node(state: AgentState):
    chunks = state.get("chunks")
    coaching_feedback = await sales_coach_agent.run(chunks=chunks)
    return {"coaching_feedback": coaching_feedback}

async def historian_node(state: AgentState):
    historian_status = await historian_agent.run(state=state)
    return {"historian_status": historian_status}

async def persistence_node(state: AgentState):
    db_status = await persistence_agent.run(
        file_path=state.get("file_path"), chunks=state.get("chunks"),
        crm_data=state.get("crm_data"), social_content=state.get("social_content"),
        email_draft=state.get("email_draft")
    )
    return {"db_save_status": db_status}

# --- Define the Final Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("parser", parser_node)
workflow.add_node("structuring", structuring_node)
workflow.add_node("chunker", chunker_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("crm", crm_node)
workflow.add_node("email", email_node)
workflow.add_node("social", social_node)
workflow.add_node("sales_coach", sales_coach_node)
workflow.add_node("historian", historian_node)
workflow.add_node("persistence", persistence_node)

# Define the flow
workflow.set_entry_point("parser")
workflow.add_edge("parser", "structuring")
workflow.add_edge("structuring", "chunker")
workflow.add_edge("chunker", "extractor")

# After extractor, FAN OUT to all final agents (except persistence)
workflow.add_edge("extractor", "crm")
workflow.add_edge("extractor", "email")
workflow.add_edge("extractor", "social")
workflow.add_edge("extractor", "sales_coach")
workflow.add_edge("extractor", "historian")

# FAN IN to the final persistence node
workflow.add_edge("crm", "persistence")
workflow.add_edge("email", "persistence")
workflow.add_edge("social", "persistence")
workflow.add_edge("sales_coach", "persistence")
workflow.add_edge("historian", "persistence")

workflow.set_finish_point("persistence")

app = workflow.compile()