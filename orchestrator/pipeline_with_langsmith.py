import asyncio
from pathlib import Path
from orchestrator.graph import app
import os

# Add LangSmith observability (just 3 env vars!)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key-here"  # Get from langsmith.com
os.environ["LANGCHAIN_PROJECT"] = "stellar-sales-system"


async def run_pipeline(file_path: Path):
    """
    Same pipeline, now with LangSmith tracing!
    Every agent call, LLM request, and state change will be visible in LangSmith UI.
    """
    print(f"--- Starting Pipeline with LangSmith Tracing for {file_path.name} ---")
    
    try:
        raw_text = file_path.read_text(encoding='utf-8')
        initial_state = {"file_path": file_path, "raw_text": raw_text}

        final_state = None
        async for event in app.astream(initial_state):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")
                if final_state is None:
                    final_state = value.copy() if value else {}
                else:
                    if value:
                        final_state.update(value)

        print("--- Pipeline Finished ---")
        print(f"🔍 View trace at: https://smith.langchain.com/")
        return final_state
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_file = Path("data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")
    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"❌ File not found at {test_file}")

