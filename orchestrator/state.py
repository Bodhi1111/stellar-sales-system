from typing import TypedDict, List, Dict, Any
from pathlib import Path

class AgentState(TypedDict):
    """
    This is the basket that carries our data through the graph.
    """
    file_path: Path
    chunks: List[str]
    extracted_data: Dict[str, Any]
    crm_data: Dict[str, Any]
    email_draft: str
    db_save_status: Dict[str, Any]
    social_content: Dict[str, Any]

    # A dictionary to hold the coaching feedback
    coaching_feedback: Dict[str, Any]