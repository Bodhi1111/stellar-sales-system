#!/usr/bin/env python3
"""
Generate a visual representation of the LangGraph pipeline.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the graph
from orchestrator.graph import app

print("🎨 Stellar Sales System - Pipeline Structure")
print("=" * 70)

try:
    # Try to generate Mermaid diagram (if available)
    from langgraph.graph import StateGraph
    
    # Get the graph structure
    print("\n📊 Visual Pipeline Flow:\n")
    print(app.get_graph().draw_mermaid())
    
    print("\n" + "=" * 70)
    print("💡 To visualize this diagram:")
    print("   1. Copy the output above")
    print("   2. Go to: https://mermaid.live/")
    print("   3. Paste the code")
    print("   4. See your pipeline visually!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n⚠️  Could not generate Mermaid diagram: {e}")
    print("\nShowing text-based pipeline structure instead:\n")
    
    # Show nodes and edges manually
    print("📋 Pipeline Nodes:")
    print("   1. structuring  → Analyzes transcript structure")
    print("   2. parser       → Parses dialogue turns")
    print("   3. chunker      → Creates parent-child chunks")
    print("   4. embedder     → Generates embeddings")
    print("   5. email        → Extracts email drafts")
    print("   6. social       → Finds social content")
    print("   7. sales_coach  → Analyzes performance")
    print("   8. crm          → Builds CRM record")
    print("   9. persistence  → Saves to database & Baserow")
    
    print("\n🔀 Pipeline Flow:")
    print("   START → structuring → parser → chunker → embedder")
    print("        → [parallel: email, social, sales_coach]")
    print("        → crm → persistence → END")

print("\n📊 For real-time observability:")
print(f"   Langfuse: http://localhost:3000")
print(f"   Click on any trace to see the execution tree!")

