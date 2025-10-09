from agents.sales_copilot.sales_copilot_agent import SalesCopilotAgent as RealSalesCopilotAgent
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import re

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

# Reasoning Engine Agents (Sprint 02)
from agents.gatekeeper.gatekeeper_agent import GatekeeperAgent
from agents.planner.planner_agent import PlannerAgent
from agents.auditor.auditor_agent import AuditorAgent
from agents.strategist.strategist_agent import StrategistAgent

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

# Reasoning Engine agents
gatekeeper_agent = GatekeeperAgent(settings)
planner_agent = PlannerAgent(settings)
auditor_agent = AuditorAgent(settings)
strategist_agent = StrategistAgent(settings)

# Real specialist agent for tool execution (Sprint 03 upgrade)

sales_copilot_agent = RealSalesCopilotAgent(settings)

# Tool mapping for the Planner (Sprint 03 - Epic 3.3)
tool_map = {
    # Multi-modal librarian (Qdrant + Neo4j)
    "sales_copilot_tool": sales_copilot_agent,
    "crm_tool": crm_agent,  # CRM analytics and metrics
    "email_tool": email_agent,  # Email draft generation
}

# --- Define Agent Nodes for the Intelligence First Workflow ---


async def structuring_node(state: AgentState) -> Dict[str, Any]:
    """
    NEW ARCHITECTURE: Runs FIRST on raw transcript
    Performs SEMANTIC NLP ANALYSIS using spaCy + transformers
    Extracts: phases, entities, topics, intent, sentiment, discourse markers
    """
    # Read raw transcript
    content = state["file_path"].read_text(encoding='utf-8')

    # Enable semantic NLP analysis (use_semantic_nlp=True)
    result = await structuring_agent.run(
        raw_transcript=content,
        use_semantic_nlp=True  # ← ENABLES NLP PROCESSOR
    )

    # Extract components from NLP analysis
    if isinstance(result, dict) and "conversation_phases" in result:
        # Full semantic NLP result
        return {
            "conversation_phases": result.get("conversation_phases", []),
            "semantic_turns": result.get("semantic_turns", []),
            "key_entities_nlp": result.get("named_entities", {}),
            "conversation_structure": result.get("document_metadata", {})
        }
    else:
        # Backward compatible (list of phases only)
        return {"conversation_phases": result}


async def parser_node(state: AgentState) -> Dict[str, Any]:
    """
    Parse transcript and ENRICH with conversation phase + semantic NLP metadata
    Receives phases + semantic_turns from StructuringAgent NLP analysis
    """
    result = await parser_agent.run(
        file_path=state["file_path"],
        conversation_phases=state.get("conversation_phases"),
        semantic_turns=state.get("semantic_turns")  # ← NLP semantic metadata
    )
    return {
        "structured_dialogue": result["structured_dialogue"],
        "transcript_id": result["transcript_id"],
        "conversation_phases": result.get("conversation_phases"),  # Passthrough
        "semantic_turns": state.get("semantic_turns"),  # Passthrough NLP metadata
        "key_entities_nlp": state.get("key_entities_nlp"),  # Passthrough
        "conversation_structure": state.get("conversation_structure")  # Passthrough
    }


async def chunker_node(state: AgentState) -> Dict[str, Any]:
    """
    Segment content with RICH metadata preservation
    Receives enriched dialogue from ParserAgent
    """
    chunks = await chunker_agent.run(
        file_path=state["file_path"],
        structured_dialogue=state.get("structured_dialogue")
    )
    return {"chunks": chunks}


async def knowledge_analyst_node(state: AgentState) -> Dict[str, Any]:
    """Extract entities from Qdrant vectors and build knowledge graph (RAG-based)"""
    result = await knowledge_analyst_agent.run(
        transcript_id=state["transcript_id"],
        file_path=state["file_path"]
    )
    # Populate both new and legacy fields for compatibility
    return {
        "extracted_entities": result.get("extracted_entities"),
        # For backward compatibility
        "extracted_data": result.get("extracted_entities")
    }


async def embedder_node(state: AgentState) -> Dict[str, Any]:
    """Generate and store embeddings in Qdrant with metadata for filtering"""
    if not state.get("transcript_id"):
        print("   - Halting embedder: missing transcript_id.")
        return {}

    # Prepare metadata for embeddings (enables filtering in RAG queries)
    # Note: extracted_data is not available yet (embedder runs BEFORE knowledge analyst)
    # We only have conversation_phases from structuring agent at this point
    metadata = {
        "client_name": "",  # Will be empty at this stage, populated later
        "meeting_date": "",  # Will be empty at this stage, populated later
        "conversation_phases": state.get("conversation_phases", [])
    }

    await embedder_agent.run(
        chunks=state["chunks"],
        transcript_id=state["transcript_id"],
        metadata=metadata
    )
    return {}

# --- Legacy Downstream Nodes ---


async def email_node(state: AgentState) -> Dict[str, Any]:
    """Generate follow-up email drafts"""
    email_draft = await email_agent.run(extracted_data=state["extracted_data"])
    return {"email_draft": email_draft}


async def social_node(state: AgentState) -> Dict[str, Any]:
    """Generate social media content"""
    # Extract text from chunk dicts for backward compatibility
    chunks = state["chunks"]
    chunk_texts = [c["text"] if isinstance(c, dict) else c for c in chunks]
    social_content = await social_agent.run(chunks=chunk_texts)
    return {"social_content": social_content}


async def sales_coach_node(state: AgentState) -> Dict[str, Any]:
    """Provide coaching feedback"""
    # Extract text from chunk dicts for backward compatibility
    chunks = state["chunks"]
    chunk_texts = [c["text"] if isinstance(c, dict) else c for c in chunks]
    coaching_feedback = await sales_coach_agent.run(chunks=chunk_texts)
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
    result = await persistence_agent.run(data={
        "file_path": state["file_path"],
        "chunks": state["chunks"],
        "crm_data": state["crm_data"],
        "social_content": state["social_content"],
        "email_draft": state["email_draft"],
        "extracted_entities": state.get("extracted_entities", {}),
        "transcript_id": state["transcript_id"]  # Use external_id from header
    })
    return {"db_save_status": result}

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

    # --- Define the Graph Edges (NEW ARCHITECTURE: Structuring-First) ---
    # CRITICAL: Structuring runs FIRST on raw transcript for semantic NLP analysis
    workflow.set_entry_point("structuring")
    workflow.add_edge("structuring", "parser")  # Parser enriches dialogue with phases
    workflow.add_edge("parser", "chunker")

    # NEW FLOW: Embedder runs FIRST to populate Qdrant (fast)
    # Then Knowledge Analyst queries the vectors (RAG-based extraction)
    workflow.add_edge("chunker", "embedder")
    workflow.add_edge("embedder", "knowledge_analyst")

    # After the knowledge analyst runs, fan out to the legacy downstream agents
    workflow.add_edge("knowledge_analyst", "email")
    workflow.add_edge("knowledge_analyst", "social")
    workflow.add_edge("knowledge_analyst", "sales_coach")

    # Converge legacy agents into the CRM agent
    workflow.add_edge(["email", "social", "sales_coach"], "crm")

    # Final persistence (no longer needs to wait for embedder separately)
    workflow.add_edge("crm", "persistence")

    workflow.add_edge("persistence", END)

    return workflow.compile()

# --- Reasoning Engine Workflow (Sprint 02) ---


def _parse_tool_call_safely(tool_call: str) -> tuple:
    """
    Safely parses a tool call string like "tool_name('argument')" without using eval().

    Returns:
        tuple: (tool_name, tool_input) or (None, None) if parsing fails
    """
    match = re.match(r"(\w+)\s*\(\s*['\"](.+?)['\"]\s*\)", tool_call)
    if match:
        return match.group(1), match.group(2)
    return None, None


async def gatekeeper_node(state: AgentState) -> Dict[str, Any]:
    """Check if user request is specific enough"""
    result = await gatekeeper_agent.run(data={"original_request": state["original_request"]})
    return {"clarification_question": result.get("clarification_question")}


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Create step-by-step execution plan"""
    result = await planner_agent.run(data={"original_request": state["original_request"]})
    return {"plan": result.get("plan", ["FINISH"])}


async def tool_executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the next tool in the plan safely"""
    print("🛠️ ToolExecutorNode: Executing the next step...")

    plan = state.get("plan", [])
    if not plan:
        return {}

    next_step = plan[0]
    tool_name, tool_input = _parse_tool_call_safely(next_step)

    if not tool_name or tool_name not in tool_map:
        error_output = {
            "error": f"Tool '{tool_name}' not found or call is malformed."}
        new_step = {
            "tool_name": tool_name or "unknown",
            "tool_input": tool_input or "",
            "tool_output": error_output
        }
    else:
        tool_agent = tool_map[tool_name]
        try:
            # All tools conform to the same run(data) signature
            result = await tool_agent.run(data={"query": tool_input})
            new_step = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": result
            }
        except Exception as e:
            new_step = {
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_output": {"error": str(e)}
            }

    return {
        "intermediate_steps": (state.get("intermediate_steps") or []) + [new_step],
        "plan": plan[1:]
    }


async def auditor_node(state: AgentState) -> Dict[str, Any]:
    """Verify the last tool output"""
    if not state.get("intermediate_steps"):
        return {}

    last_step = state["intermediate_steps"][-1]
    result = await auditor_agent.run(data={
        "original_request": state["original_request"],
        "last_step": last_step
    })

    verification_history = state.get("verification_history") or []
    return {
        "verification_history": verification_history + [result]
    }


async def replanner_node(state: AgentState) -> Dict[str, Any]:
    """Clears the plan to force replanning"""
    print("   🔄 Clearing plan for replanning...")
    return {"plan": []}


async def strategist_node(state: AgentState) -> Dict[str, Any]:
    """Synthesize final answer from intermediate steps"""
    result = await strategist_agent.run(data={
        "original_request": state["original_request"],
        "intermediate_steps": state.get("intermediate_steps", [])
    })
    return {"final_response": result["final_response"]}


def router_node(state: AgentState) -> str:
    """
    Routes the workflow based on current state.
    This is a pure function (not async) that returns the next node name.
    """
    # If there's a clarification question, end workflow
    if state.get("clarification_question"):
        print(f"   ❓ Clarification needed: {state['clarification_question']}")
        return END

    # If plan is empty or only has FINISH, go to strategist
    plan = state.get("plan", [])
    if not plan or plan[0] == "FINISH":
        return "strategist"

    # Check last verification if exists
    verification_history = state.get("verification_history", [])
    if verification_history:
        last_verification = verification_history[-1]
        # If confidence is low (< 3), re-plan
        if last_verification["confidence_score"] < 3:
            return "replanner"

    # Continue with next tool
    return "tool_executor"


def create_reasoning_workflow():
    """
    Creates the Reasoning Engine workflow for query answering:
    1. Gatekeeper checks query clarity
    2. Planner creates execution plan
    3. Loop: Tool Executor → Auditor → Router
    4. Router decides: continue, re-plan, or synthesize
    5. Strategist generates final answer
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("gatekeeper", gatekeeper_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("auditor", auditor_node)
    workflow.add_node("replanner", replanner_node)
    workflow.add_node("strategist", strategist_node)

    # Define edges
    workflow.set_entry_point("gatekeeper")
    workflow.add_edge("gatekeeper", "planner")
    workflow.add_edge("planner", "tool_executor")
    workflow.add_edge("tool_executor", "auditor")

    # Conditional routing after auditor
    workflow.add_conditional_edges(
        "auditor",
        router_node,
        {
            "tool_executor": "tool_executor",
            "replanner": "replanner",
            "strategist": "strategist",
            END: END
        }
    )

    # Replanner loops back to planner to create new plan
    workflow.add_edge("replanner", "planner")

    # Strategist ends the workflow
    workflow.add_edge("strategist", END)

    return workflow.compile()


# Export both workflows
app = create_master_workflow()
reasoning_app = create_reasoning_workflow()
