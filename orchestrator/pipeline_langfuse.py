import asyncio
import os
from pathlib import Path

# Load settings first
from config.settings import settings

# Enable Langfuse tracing if configured
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    
    # Initialize Langfuse
    from langfuse.callback import CallbackHandler
    langfuse_handler = CallbackHandler()
    
    print(f"🔍 Langfuse tracing enabled: {settings.LANGFUSE_HOST}")
else:
    langfuse_handler = None
    print("ℹ️  Langfuse tracing disabled (no API keys found)")

# Import graph AFTER setting env vars
from orchestrator.graph import app


async def run_pipeline(file_path: Path):
    """
    Runs the full LangGraph pipeline with Langfuse tracing.
    Every agent, LLM call, and state change will be visible in Langfuse UI.
    """
    print(f"--- Starting Pipeline with Langfuse for {file_path.name} ---")
    
    try:
        raw_text = file_path.read_text(encoding='utf-8')
        initial_state = {"file_path": file_path, "raw_text": raw_text}

        final_state = None
        
        # Configure LangGraph with Langfuse callback
        config = {}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]
        
        async for event in app.astream(initial_state, config=config):
            for key, value in event.items():
                print(f"--- Node '{key}' Finished ---")
                if final_state is None:
                    final_state = value.copy() if value else {}
                else:
                    if value:
                        final_state.update(value)

        print("--- Pipeline Finished ---")
        
        if langfuse_handler:
            # Flush traces to Langfuse
            langfuse_handler.langfuse.flush()
            print(f"🔍 View execution trace at: {settings.LANGFUSE_HOST}")
            
        return final_state
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if langfuse_handler:
            langfuse_handler.langfuse.flush()
            
        return None


if __name__ == "__main__":
    test_file = Path("data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")
    if test_file.exists():
        asyncio.run(run_pipeline(file_path=test_file))
    else:
        print(f"❌ File not found at {test_file}")
        print("Please provide a test transcript file.")

