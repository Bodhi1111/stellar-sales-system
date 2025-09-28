from typing import TypedDict, List, Dict, Any
from pathlib import Path

class AgentState(TypedDict):
    """
    This is the basket that carries our data through the graph.
    """
    # --- Initial Input & Preprocessing ---
    file_path: Path
    raw_text: str
    structured_dialogue: List[Dict[str, Any]]
    conversation_phases: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]

    # --- Parallel Agent Outputs ---
    extracted_data: Dict[str, Any]
    crm_data: Dict[str, Any]
    email_draft: str
    social_content: Dict[str, Any]
    coaching_feedback: Dict[str, Any]

    # --- Persistence Agent Outputs ---
    db_save_status: Dict[str, Any]
    historian_status: Dict[str, Any] # New field