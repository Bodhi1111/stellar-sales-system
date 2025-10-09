import asyncio
from pathlib import Path
from orchestrator.graph import app


async def run_pipeline(file_path: Path):
    """
    Reads a file and runs the full, advanced LangGraph pipeline.
    Returns the final state after pipeline completion.
    """
    print(f"--- Starting Advanced Pipeline for {file_path.name} ---")
    try:
        # Read the raw text from the file first
        raw_text = file_path.read_text(encoding='utf-8')

        # Provide the initial state for our new graph
        initial_state = {"file_path": file_path, "raw_text": raw_text}

        # Run the graph and collect final state
        final_state = None
        async for event in app.astream(initial_state):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")
                # Update final_state with latest values
                if final_state is None:
                    final_state = value.copy() if value else {}
                else:
                    if value:
                        final_state.update(value)

        print("--- Advanced Pipeline Finished ---")
        return final_state
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred in the pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_file = Path("data/transcripts/test_sprint01.txt")
    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"❌ ERROR: Test file not found at {test_file}")
        print(
            "Please create a test file with proper header format including transcript_id.")
