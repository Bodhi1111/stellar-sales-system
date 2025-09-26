from config.settings import settings
from agents.chunker.chunker import ChunkerAgent
from orchestrator.state import AgentState
from langgraph.graph import StateGraph
from agents.extractor.extractor import ExtractorAgent
# Initialize our agents once to be used by the nodes
chunker_agent = ChunkerAgent(settings)
extractor_agent = ExtractorAgent(settings)

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
    
# Define a new graph
workflow = StateGraph(AgentState)

# Add our chunker function as a node
workflow.add_node("chunker", chunker_node)

# Set the entry point for the graph
workflow.set_entry_point("chunker")

# Set the finish point for the graph
workflow.set_finish_point("chunker")

# Compile the graph into a runnable app
app = workflow.compile()