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