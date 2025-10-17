import asyncio
import os
from pathlib import Path

# Load settings first to get observability config
from config.settings import settings

# Configure observability
langfuse_handler = None

# Enable Langfuse tracing if configured (local, self-hosted)
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    
    try:
        from langfuse.callback import CallbackHandler
        # CallbackHandler automatically uses environment variables
        langfuse_handler = CallbackHandler()
        print(f"🔍 Langfuse tracing enabled (local): {settings.LANGFUSE_HOST}")
    except Exception as e:
        print(f"⚠️  Langfuse handler failed to initialize: {e}")
        print(f"ℹ️  Continuing without tracing...")

# Enable LangSmith tracing if configured (cloud)
elif settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    print(f"🔍 LangSmith tracing enabled for project: {settings.LANGCHAIN_PROJECT}")
else:
    print("ℹ️  Observability tracing disabled (no API keys found)")

# Import graph AFTER setting env vars
from orchestrator.graph import app


async def run_pipeline(file_path: Path):
    """
    Reads a file and runs the full, advanced LangGraph pipeline with observability.
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
        
        # Configure callbacks for observability
        config = {}
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}
        
        async for event in app.astream(initial_state, config=config):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")
                # Update final_state with latest values
                if final_state is None:
                    final_state = value.copy() if value else {}
                else:
                    if value:
                        final_state.update(value)

        print("--- Advanced Pipeline Finished ---")
        
        # Flush Langfuse traces
        if langfuse_handler:
            langfuse_handler.flush()
            print(f"📤 Flushed traces to Langfuse")
        
        if settings.LANGFUSE_PUBLIC_KEY:
            print(f"🔍 View execution trace at: {settings.LANGFUSE_HOST}")
        elif settings.LANGCHAIN_API_KEY:
            print(f"🔍 View execution trace at: https://smith.langchain.com/")
        return final_state
    except Exception as e:
        print(f"❌ ERROR: An unexpected error occurred in the pipeline: {e}")
        import traceback
        traceback.print_exc()
        
        # Flush traces even on error
        if langfuse_handler:
            langfuse_handler.flush()
        
        return None

if __name__ == "__main__":
    test_file = Path("data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")
    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"❌ ERROR: Test file not found at {test_file}")
        print(
            "Please create a test file with proper header format including transcript_id.")
