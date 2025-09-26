import asyncio
from pathlib import Path
from orchestrator.graph import app # Import our compiled graph

async def run_pipeline(file_path: Path):
    """
    Runs the LangGraph pipeline with a given file path.
    """
    print(f"--- Starting Pipeline for {file_path.name} ---")

    # This is the initial "data basket" we give to the graph
    initial_state = {"file_path": file_path}

    # astream() runs the graph from the entry point to the end
    async for event in app.astream(initial_state):
        # This will print the output from each node as it runs
        for key, value in event.items():
            print(f"Node '{key}' finished. Final state:")
            print(value)

    print("--- Pipeline Finished ---")


if __name__ == "__main__":
    # The test file we created earlier
    test_file = Path("data/transcripts/test_file.txt")

    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"Error: Test file not found at {test_file}")