from config.settings import settings
from agents.chunker.chunker import ChunkerAgent
from orchestrator.state import AgentState
from langgraph.graph import StateGraph
from agents.extractor.extractor import ExtractorAgent
from agents.crm.crm_agent import CRMAgent
from agents.email.email_agent import EmailAgent
from agents.persistence.persistence_agent import PersistenceAgent
from agents.social.social_agent import SocialAgent
from agents.sales_coach.sales_coach_agent import SalesCoachAgent

# Initialize our agents once to be used by the nodes
chunker_agent = ChunkerAgent(settings)
extractor_agent = ExtractorAgent(settings)
crm_agent = CRMAgent(settings)
email_agent = EmailAgent(settings)
persistence_agent = PersistenceAgent(settings)
social_agent = SocialAgent(settings)
sales_coach_agent = SalesCoachAgent(settings)

async def chunker_node(state: AgentState):
    """
    This node runs the ChunkerAgent.
    It takes the file_path from the state and adds the chunks back.
    """
    print("--- Running Chunker Node ---")

    # 1. The "Pickup Station"
    file_path = state.get("file_path")

    # 2. Do the work
    chunks = await chunker_agent.run(file_path=file_path)

    # 3. The "Drop-off Station"
    return {"chunks": chunks}

async def extractor_node(state: AgentState):
    """
    This node runs the ExtractorAgent.
    It takes chunks from the state and adds the extracted_data back.
    """
    print("--- Running Extractor Node ---")
    chunks = state.get("chunks")

    extracted_data = await extractor_agent.run(chunks=chunks)

    return {"extracted_data": extracted_data}

async def crm_node(state: AgentState):
    """
    This node runs the CRMAgent.
    It takes extracted_data from the state and adds the crm_data back.
    """
    print("--- Running CRM Node ---")
    extracted_data = state.get("extracted_data")

    crm_data = await crm_agent.run(extracted_data=extracted_data)

    return {"crm_data": crm_data}

async def email_node(state: AgentState):
    """
    This node runs the EmailAgent.
    """
    print("--- Running Email Node ---")
    extracted_data = state.get("extracted_data")

    email_draft = await email_agent.run(extracted_data=extracted_data)

    return {"email_draft": email_draft}

async def persistence_node(state: AgentState):
    """
    This node runs the PersistenceAgent to save all data.
    """
    print("--- Running Persistence Node ---")

    # Gather all the necessary data from the state basket
    db_status = await persistence_agent.run(
        file_path=state.get("file_path"),
        chunks=state.get("chunks"),
        crm_data=state.get("crm_data"),
        social_content=state.get("social_content"),
        email_draft=state.get("email_draft")
    )

    return {"db_save_status": db_status}

async def social_node(state: AgentState):
    """
    This node runs the SocialAgent.
    """
    print("--- Running Social Node ---")
    chunks = state.get("chunks")

    social_content = await social_agent.run(chunks=chunks)

    return {"social_content": social_content}

async def sales_coach_node(state: AgentState):
    """
    This node runs the SalesCoachAgent.
    """
    print("--- Running Sales Coach Node ---")
    chunks = state.get("chunks")

    coaching_feedback = await sales_coach_agent.run(chunks=chunks)

    return {"coaching_feedback": coaching_feedback}

# Define a new graph
workflow = StateGraph(AgentState)

# Add all the nodes
workflow.add_node("chunker", chunker_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("crm", crm_node)
workflow.add_node("email", email_node)
workflow.add_node("social", social_node)
workflow.add_node("sales_coach", sales_coach_node)
workflow.add_node("persistence", persistence_node)

# Define the flow of the graph
workflow.set_entry_point("chunker")
workflow.add_edge("chunker", "extractor")

# After the extractor, fan out to the parallel nodes
workflow.add_edge("extractor", "crm")
workflow.add_edge("extractor", "email")
workflow.add_edge("extractor", "social")
workflow.add_edge("extractor", "sales_coach")

# After each branch is done, they all join at the persistence node
workflow.add_edge("crm", "persistence")
workflow.add_edge("email", "persistence")
workflow.add_edge("social", "persistence")
workflow.add_edge("sales_coach", "persistence")

# The pipeline now finishes after saving the data
workflow.set_finish_point("persistence")

# Compile the graph
app = workflow.compile()