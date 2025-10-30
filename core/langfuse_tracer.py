"""
LangFuse Tracing Utilities for Stellar Sales System

This module provides utilities to trace agent execution in the LangGraph pipeline.
It wraps agent calls with observability spans that capture:
- Execution time and performance metrics
- Input/output data (with size limits to prevent huge payloads)
- Errors and exceptions with full stack traces
- Custom metadata (agent name, model used, etc.)

Key Concepts:
- TRACE: A complete pipeline execution (one transcript processing)
- SPAN: An individual agent's execution within the trace
- GENERATION: An LLM call (automatically captured by LangFuse callback)

For Beginners:
Think of tracing like a detailed activity log. When your pipeline runs, LangFuse
creates a "trace" (like a log file) that shows:
1. What happened (which agents ran)
2. When it happened (timestamps and durations)
3. What data was passed between agents (inputs/outputs)
4. If anything went wrong (errors with details)

This helps you debug issues and find bottlenecks in your pipeline.
"""

import time
import json
import traceback
from typing import Dict, Any, Optional, Callable
from functools import wraps
from pathlib import Path


class LangFuseTracer:
    """
    Utility class for wrapping agent execution with LangFuse tracing.
    
    This class creates "spans" for each agent execution. A span is like a chapter
    in a book - it has a start, an end, and tells part of the story.
    
    Usage Example:
        tracer = LangFuseTracer(langfuse_client, trace_id)
        result = await tracer.trace_agent(
            agent_name="ParserAgent",
            agent_function=parser_agent.run,
            input_data={"file_path": "transcript.txt"},
            metadata={"order": 1}
        )
    """
    
    def __init__(self, langfuse_client: Optional[Any] = None, trace_id: Optional[str] = None):
        """
        Initialize the tracer.
        
        Args:
            langfuse_client: The LangFuse client instance (optional, for manual tracing)
            trace_id: The trace ID to associate spans with (optional)
        """
        self.langfuse_client = langfuse_client
        self.trace_id = trace_id
        self.span_count = 0
        
    def _truncate_data(self, data: Any, max_length: int = 5000) -> str:
        """
        Truncate data to prevent huge payloads in LangFuse UI.
        
        Why truncate?
        If an agent processes a 50KB transcript, we don't want to store all 50KB
        in LangFuse for every span. Instead, we store a preview (first 5000 chars)
        with a note that it was truncated.
        
        Args:
            data: Any data to truncate (dict, list, string, etc.)
            max_length: Maximum length of the string representation
            
        Returns:
            Truncated string representation of the data
        """
        try:
            # Convert data to string representation
            if isinstance(data, (dict, list)):
                data_str = json.dumps(data, indent=2, default=str)
            else:
                data_str = str(data)
            
            # Truncate if too long
            if len(data_str) > max_length:
                return data_str[:max_length] + f"\n\n... [TRUNCATED - Original length: {len(data_str)} chars]"
            
            return data_str
        except Exception as e:
            return f"[Error converting data to string: {e}]"
    
    def _extract_metadata(self, agent_name: str, input_data: Dict[str, Any], output_data: Any) -> Dict[str, Any]:
        """
        Extract useful metadata from agent inputs and outputs.
        
        This helps you understand what happened without reading through all the data.
        For example: "How many chunks did the chunker create?" or "What's the transcript ID?"
        
        Args:
            agent_name: Name of the agent
            input_data: Agent's input data
            output_data: Agent's output data
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            "agent_name": agent_name,
            "span_order": self.span_count
        }
        
        # Extract transcript ID if available
        if "transcript_id" in input_data:
            metadata["transcript_id"] = input_data["transcript_id"]
        
        # Extract file information if available
        if "file_path" in input_data:
            file_path = input_data["file_path"]
            if isinstance(file_path, Path):
                metadata["filename"] = file_path.name
                metadata["file_size_bytes"] = file_path.stat().st_size if file_path.exists() else 0
        
        # Extract output size metrics
        if isinstance(output_data, dict):
            metadata["output_keys"] = list(output_data.keys())
            
            # Count chunks if present
            if "chunks" in output_data:
                chunks = output_data["chunks"]
                if isinstance(chunks, list):
                    metadata["chunks_count"] = len(chunks)
            
            if "chunks_data" in output_data:
                chunks_data = output_data["chunks_data"]
                if isinstance(chunks_data, dict):
                    metadata["child_chunks_count"] = len(chunks_data.get("child_chunks", []))
                    metadata["parent_chunks_count"] = len(chunks_data.get("parent_chunks", []))
            
            # Extract structured dialogue count
            if "structured_dialogue" in output_data:
                dialogue = output_data["structured_dialogue"]
                if isinstance(dialogue, list):
                    metadata["dialogue_turns"] = len(dialogue)
        
        return metadata
    
    async def trace_agent(
        self,
        agent_name: str,
        agent_function: Callable,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trace an agent's execution with detailed observability.
        
        This is the main function you'll use. It wraps an agent's execution with
        timing, error handling, and data capture.
        
        Args:
            agent_name: Human-readable name of the agent (e.g., "ParserAgent")
            agent_function: The agent's run() method to execute
            input_data: Dictionary of input data to pass to the agent
            metadata: Optional additional metadata to attach
            
        Returns:
            Dictionary containing the agent's output
            
        Raises:
            Exception: Re-raises any exception from the agent after logging it
        """
        self.span_count += 1
        start_time = time.time()
        
        print(f"\n{'='*70}")
        print(f"🔍 TRACING: {agent_name} (Span #{self.span_count})")
        print(f"{'='*70}")
        
        try:
            # Execute the agent
            print(f"   ⏳ Starting {agent_name}...")
            result = await agent_function(**input_data)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Extract metadata
            extracted_metadata = self._extract_metadata(agent_name, input_data, result)
            if metadata:
                extracted_metadata.update(metadata)
            extracted_metadata["execution_time_seconds"] = round(execution_time, 2)
            extracted_metadata["status"] = "success"
            
            # Log summary
            print(f"   ✅ {agent_name} completed in {execution_time:.2f}s")
            print(f"   📊 Metadata: {json.dumps(extracted_metadata, indent=2)}")
            
            # Create span in LangFuse (if client available)
            if self.langfuse_client and self.trace_id:
                try:
                    self.langfuse_client.span(
                        trace_id=self.trace_id,
                        name=agent_name,
                        input=self._truncate_data(input_data),
                        output=self._truncate_data(result),
                        metadata=extracted_metadata,
                        start_time=start_time,
                        end_time=time.time()
                    )
                except Exception as e:
                    print(f"   ⚠️  Warning: Failed to create LangFuse span: {e}")
            
            return result
            
        except Exception as e:
            # Calculate execution time even on failure
            execution_time = time.time() - start_time
            
            # Extract error information
            error_trace = traceback.format_exc()
            error_metadata = self._extract_metadata(agent_name, input_data, None)
            if metadata:
                error_metadata.update(metadata)
            error_metadata.update({
                "execution_time_seconds": round(execution_time, 2),
                "status": "error",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "error_trace": error_trace
            })
            
            # Log error
            print(f"   ❌ {agent_name} failed after {execution_time:.2f}s")
            print(f"   🐛 Error: {type(e).__name__}: {e}")
            print(f"   📊 Metadata: {json.dumps({k: v for k, v in error_metadata.items() if k != 'error_trace'}, indent=2)}")
            
            # Create error span in LangFuse (if client available)
            if self.langfuse_client and self.trace_id:
                try:
                    self.langfuse_client.span(
                        trace_id=self.trace_id,
                        name=f"{agent_name} (FAILED)",
                        input=self._truncate_data(input_data),
                        output=f"ERROR: {type(e).__name__}: {e}\n\n{error_trace}",
                        metadata=error_metadata,
                        start_time=start_time,
                        end_time=time.time(),
                        level="ERROR"
                    )
                except Exception as span_error:
                    print(f"   ⚠️  Warning: Failed to create error span: {span_error}")
            
            # Re-raise the exception so the pipeline can handle it
            raise


def create_tracer(langfuse_client: Optional[Any] = None, trace_name: Optional[str] = None) -> LangFuseTracer:
    """
    Factory function to create a tracer instance.
    
    This is a helper function that creates a tracer and optionally starts a new trace.
    
    Args:
        langfuse_client: The LangFuse client instance
        trace_name: Name for the trace (e.g., "Pipeline: transcript.txt")
        
    Returns:
        Configured LangFuseTracer instance
    """
    trace_id = None
    
    if langfuse_client and trace_name:
        try:
            trace = langfuse_client.trace(name=trace_name)
            trace_id = trace.id
            print(f"🔍 Created LangFuse trace: {trace_name}")
            print(f"   Trace ID: {trace_id}")
        except Exception as e:
            print(f"⚠️  Warning: Failed to create trace: {e}")
    
    return LangFuseTracer(langfuse_client, trace_id)


# Decorator for automatic agent tracing (advanced usage)
def trace_agent(agent_name: str):
    """
    Decorator to automatically trace an agent's run() method.
    
    This is an advanced feature. For now, you can ignore this and use
    the trace_agent() method directly.
    
    Usage:
        @trace_agent("MyAgent")
        async def run(self, **kwargs):
            # agent code here
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simplified decorator - the main tracing happens
            # in the LangFuseTracer.trace_agent() method
            return await func(*args, **kwargs)
        return wrapper
    return decorator


