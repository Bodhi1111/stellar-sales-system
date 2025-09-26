from typing import TypedDict, List, Dict, Any
from pathlib import Path

class AgentState(TypedDict):
    """
    This is the basket that carries our data through the graph.
    """
    # The path to the file being processed
    file_path: Path

    # A list to hold the text chunks after the chunker runs
    chunks: List[str]

    # A dictionary to hold the data extracted by the LLM
    extracted_data: Dict[str, Any]