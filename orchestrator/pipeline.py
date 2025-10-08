import asyncio
from pathlib import Path
from orchestrator.graph import app


async def run_pipeline(file_path: Path):
    """
    Reads a file and runs the full, advanced LangGraph pipeline.
    """
    print(f"--- Starting Advanced Pipeline for {file_path.name} ---")
    try:
        # Read the raw text from the file first
        raw_text = file_path.read_text(encoding='utf-8')

        # Provide the initial state for our new graph
        initial_state = {"file_path": file_path, "raw_text": raw_text}

        # Run the graph
        async for event in app.astream(initial_state):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")

        print("--- Advanced Pipeline Finished ---")
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred in the pipeline: {e}")

if __name__ == "__main__":
    test_file = Path("data/transcripts/test_sprint01.txt")
    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"❌ ERROR: Test file not found at {test_file}")
        print(
            "Please create a test file with proper header format including transcript_id.")
