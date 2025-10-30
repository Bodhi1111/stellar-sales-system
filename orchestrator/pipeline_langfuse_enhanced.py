"""
Enhanced LangFuse Pipeline Runner for Stellar Sales System

This module provides comprehensive observability for the ingestion pipeline.
It traces each agent's execution with detailed metrics, timing, and error handling.

WHAT IS THIS FILE?
==================
This is an enhanced version of the standard pipeline that includes full tracing
with LangFuse. When you run this instead of the regular pipeline.py, you'll get:

1. Visual timeline of all agent executions in LangFuse UI
2. Detailed metrics for each agent (execution time, data sizes, etc.)
3. Complete error tracking with stack traces
4. Ability to compare pipeline runs and identify bottlenecks

WHEN TO USE THIS?
=================
- During development to debug issues
- When optimizing pipeline performance
- When you want to understand how data flows through agents
- When tracking down why a transcript failed to process

WHEN TO USE REGULAR pipeline.py?
================================
- In production (less overhead)
- When you don't need detailed tracing
- When LangFuse is not available

HOW IT WORKS:
=============
1. Initializes LangFuse client with your API keys from .env
2. Creates a "trace" (one complete pipeline run)
3. Wraps each agent call with a "span" (timing and metadata)
4. Sends all data to LangFuse for visualization
5. Prints progress to console in real-time

ARCHITECTURE NOTE:
==================
This file doesn't modify any agents. It wraps their execution with observability
using the LangFuseTracer utility class. All agents work exactly as they do in
the normal pipeline.
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Load settings first to get configuration
from config.settings import settings

# Initialize LangFuse if configured
langfuse_client = None
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    # Set environment variables for LangFuse SDK
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST
    
    try:
        from langfuse import Langfuse
        from langfuse.callback import CallbackHandler
        
        # Create LangFuse client for manual tracing
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
        
        # Create callback handler for LangChain/LangGraph integration
        langfuse_handler = CallbackHandler(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
        
        print(f"🔍 LangFuse Observability Enabled")
        print(f"   Host: {settings.LANGFUSE_HOST}")
        print(f"   View traces at: {settings.LANGFUSE_HOST}/traces")
        print()
        
    except ImportError:
        print("⚠️  LangFuse package not installed. Run: pip install langfuse>=2.0.0")
        langfuse_client = None
        langfuse_handler = None
    except Exception as e:
        print(f"⚠️  Failed to initialize LangFuse: {e}")
        langfuse_client = None
        langfuse_handler = None
else:
    print("ℹ️  LangFuse tracing disabled (no API keys in .env)")
    print("   To enable: Add LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to .env")
    print("   See docs/LANGFUSE_SETUP.md for instructions")
    print()
    langfuse_handler = None

# Import orchestrator components
from orchestrator.graph import app
from orchestrator.state import AgentState

# Import our custom tracer utility
from core.langfuse_tracer import create_tracer


async def run_pipeline_with_tracing(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Run the full ingestion pipeline with comprehensive LangFuse tracing.
    
    This function orchestrates the entire pipeline and creates detailed traces
    for every agent execution.
    
    PIPELINE FLOW:
    ==============
    1. Structuring Agent  - Semantic NLP analysis of raw transcript
    2. Parser Agent       - Extract header metadata and parse dialogue
    3. Chunker Agent      - Create parent-child chunk hierarchy
    4. Embedder Agent     - Generate embeddings and store in Qdrant
    5. Email Agent        - Generate follow-up email draft
    6. Social Agent       - Create social media content
    7. Sales Coach Agent  - Provide coaching feedback
    8. CRM Agent          - Consolidate all data into CRM format
    9. Persistence Agent  - Save to PostgreSQL and sync to Baserow
    
    Args:
        file_path: Path to the transcript file to process
        
    Returns:
        Final state dictionary with all processed data, or None if failed
    """
    
    print("="*80)
    print(f"🚀 STARTING ENHANCED PIPELINE WITH LANGFUSE TRACING")
    print("="*80)
    print(f"📄 File: {file_path.name}")
    print(f"📏 Size: {file_path.stat().st_size if file_path.exists() else 0} bytes")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Verify file exists
    if not file_path.exists():
        print(f"❌ ERROR: File not found at {file_path}")
        return None
    
    try:
        # Read the transcript
        raw_text = file_path.read_text(encoding='utf-8')
        print(f"✅ Loaded transcript ({len(raw_text)} characters)")
        print()
        
        # Create initial state for LangGraph
        initial_state: AgentState = {
            "file_path": file_path,
            "raw_text": raw_text,
            # All other fields start as None/empty
            "transcript_id": None,
            "chunks": None,
            "chunks_data": None,
            "header_metadata": None,
            "structured_dialogue": None,
            "conversation_phases": None,
            "extracted_data": None,
            "crm_data": None,
            "email_draft": None,
            "social_content": None,
            "coaching_feedback": None,
            "db_save_status": None,
            "semantic_turns": None,
            "key_entities_nlp": None,
            "conversation_structure": None,
            "original_request": None,
            "extracted_entities": None,
            "plan": None,
            "intermediate_steps": None,
            "verification_history": None,
            "clarification_question": None,
            "final_response": None,
            "historian_status": None
        }
        
        # Create LangFuse trace for this pipeline run
        trace_name = f"Pipeline: {file_path.name}"
        if langfuse_client:
            trace = langfuse_client.trace(
                name=trace_name,
                metadata={
                    "pipeline_type": "ingestion",
                    "filename": file_path.name,
                    "file_size_bytes": file_path.stat().st_size,
                    "started_at": datetime.now().isoformat(),
                    "pipeline_version": "enhanced_v1"
                }
            )
            trace_id = trace.id
            print(f"🔍 Created LangFuse trace: {trace_name}")
            print(f"   Trace ID: {trace_id}")
            print(f"   View at: {settings.LANGFUSE_HOST}/trace/{trace_id}")
            print()
        else:
            trace_id = None
        
        # Configure LangGraph with LangFuse callback
        # This automatically traces LLM calls within agents
        config = {}
        if langfuse_handler:
            config = {"callbacks": [langfuse_handler]}
        
        # Run the LangGraph pipeline
        # The pipeline will execute agents in sequence/parallel as defined in graph.py
        print("🏃 Running pipeline agents...")
        print("   (Watch progress in LangFuse UI for detailed metrics)")
        print()
        
        final_state = None
        agent_count = 0
        
        # Stream events from the pipeline
        # Each event represents an agent completion
        async for event in app.astream(initial_state, config=config):
            for agent_name, state_update in event.items():
                agent_count += 1
                print(f"{'─'*80}")
                print(f"✅ Agent '{agent_name}' completed (#{agent_count})")
                
                # Show key metrics from this agent's output
                if state_update:
                    if "transcript_id" in state_update and state_update["transcript_id"]:
                        print(f"   📋 Transcript ID: {state_update['transcript_id']}")
                    if "chunks_data" in state_update and state_update["chunks_data"]:
                        chunks_data = state_update["chunks_data"]
                        if isinstance(chunks_data, dict):
                            child_count = len(chunks_data.get("child_chunks", []))
                            parent_count = len(chunks_data.get("parent_chunks", []))
                            print(f"   📦 Chunks: {child_count} child, {parent_count} parent")
                    if "crm_data" in state_update and state_update["crm_data"]:
                        crm_data = state_update["crm_data"]
                        if isinstance(crm_data, dict):
                            client_name = crm_data.get("client_name", "Unknown")
                            print(f"   👤 Client: {client_name}")
                
                print(f"{'─'*80}")
                print()
                
                # Update final state
                if final_state is None:
                    final_state = state_update.copy() if state_update else {}
                else:
                    if state_update:
                        final_state.update(state_update)
        
        # Pipeline completed successfully
        end_time = datetime.now()
        print("="*80)
        print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"🕐 Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total agents executed: {agent_count}")
        print()
        
        # Finalize LangFuse trace
        if langfuse_client and trace_id:
            try:
                # Update trace with completion metadata
                langfuse_client.trace(
                    id=trace_id,
                    metadata={
                        "status": "success",
                        "agents_executed": agent_count,
                        "completed_at": end_time.isoformat(),
                        "transcript_id": final_state.get("transcript_id") if final_state else None
                    }
                )
                
                # Flush all pending traces to LangFuse server
                langfuse_client.flush()
                
                print(f"🔍 LangFuse Trace Updated")
                print(f"   View complete trace at: {settings.LANGFUSE_HOST}/trace/{trace_id}")
                print()
                
            except Exception as e:
                print(f"⚠️  Warning: Failed to finalize trace: {e}")
                print()
        
        return final_state
        
    except KeyboardInterrupt:
        print()
        print("="*80)
        print("⚠️  PIPELINE INTERRUPTED BY USER")
        print("="*80)
        
        if langfuse_client:
            langfuse_client.flush()
        
        return None
        
    except Exception as e:
        print()
        print("="*80)
        print(f"❌ PIPELINE FAILED")
        print("="*80)
        print(f"🐛 Error: {type(e).__name__}: {e}")
        print()
        
        # Log error to LangFuse
        if langfuse_client and trace_id:
            try:
                import traceback
                langfuse_client.trace(
                    id=trace_id,
                    metadata={
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "error_trace": traceback.format_exc()
                    }
                )
                langfuse_client.flush()
                print(f"🔍 Error logged to LangFuse: {settings.LANGFUSE_HOST}/trace/{trace_id}")
                print()
            except Exception as trace_error:
                print(f"⚠️  Warning: Failed to log error to LangFuse: {trace_error}")
                print()
        
        # Print stack trace for debugging
        import traceback
        traceback.print_exc()
        
        return None


async def run_pipeline(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Main entry point - wraps run_pipeline_with_tracing for compatibility.
    
    This function has the same signature as the standard pipeline.py so you
    can use it as a drop-in replacement.
    
    Args:
        file_path: Path to transcript file
        
    Returns:
        Final pipeline state or None if failed
    """
    return await run_pipeline_with_tracing(file_path)


if __name__ == "__main__":
    """
    Command-line interface for running the enhanced pipeline.
    
    Usage:
        python orchestrator/pipeline_langfuse_enhanced.py
    
    This will process the default test transcript. To process a different file,
    modify the test_file path below.
    """
    
    # Default test file
    test_file = Path("data/transcripts/pipeline_test.txt")
    
    # Alternative test files you can use:
    # test_file = Path("data/transcripts/test_sprint01.txt")
    # test_file = Path("data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")
    
    if test_file.exists():
        print(f"📋 Processing test transcript: {test_file.name}")
        print()
        
        # Run the pipeline
        result = asyncio.run(run_pipeline(file_path=test_file))
        
        if result:
            print()
            print("="*80)
            print("📊 PIPELINE RESULTS SUMMARY")
            print("="*80)
            
            if result.get("transcript_id"):
                print(f"   Transcript ID: {result['transcript_id']}")
            
            if result.get("crm_data"):
                crm_data = result["crm_data"]
                if isinstance(crm_data, dict):
                    print(f"   Client: {crm_data.get('client_name', 'Unknown')}")
                    print(f"   Deal Amount: ${crm_data.get('deal', 0)}")
                    print(f"   Outcome: {crm_data.get('outcome', 'Unknown')}")
            
            if result.get("db_save_status"):
                print(f"   Database: {result['db_save_status'].get('status', 'Unknown')}")
            
            print("="*80)
            print()
            print("✅ Pipeline execution complete!")
            print(f"🔍 View detailed trace at: {settings.LANGFUSE_HOST}/traces")
            
        else:
            print()
            print("❌ Pipeline failed - check logs above for details")
            print(f"🔍 Check LangFuse for error details: {settings.LANGFUSE_HOST}/traces")
    
    else:
        print(f"❌ Test file not found: {test_file}")
        print()
        print("Available transcripts:")
        transcripts_dir = Path("data/transcripts")
        if transcripts_dir.exists():
            for f in transcripts_dir.glob("*.txt"):
                print(f"   - {f.name}")
        print()
        print("Update the test_file path in this script to process a different file.")


