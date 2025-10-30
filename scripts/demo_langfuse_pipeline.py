#!/usr/bin/env python3
"""
LangFuse Pipeline Demo

This script demonstrates the enhanced pipeline with full LangFuse tracing.
It provides a beginner-friendly experience with:
- Real-time progress updates
- Explanation of what's happening
- Direct links to view traces in LangFuse UI
- Summary report after completion

Perfect for:
- First-time LangFuse users
- Demonstrating the system to others
- Verifying your setup works end-to-end

Usage:
    python scripts/demo_langfuse_pipeline.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def print_banner():
    """Print welcome banner"""
    print()
    print("=" * 80)
    print("  🚀 LANGFUSE PIPELINE DEMONSTRATION")
    print("=" * 80)
    print()
    print("This demo will:")
    print("  1. Process a test transcript through the full pipeline")
    print("  2. Send detailed trace data to LangFuse")
    print("  3. Show you where to view the results")
    print()
    print(f"LangFuse UI: {settings.LANGFUSE_HOST}")
    print()
    print("=" * 80)
    print()


def select_test_file():
    """Let user select a test transcript"""
    transcripts_dir = Path("data/transcripts")
    
    if not transcripts_dir.exists():
        print(f"❌ Error: Transcripts directory not found: {transcripts_dir}")
        return None
    
    # Find available transcripts
    transcripts = list(transcripts_dir.glob("*.txt"))
    
    if not transcripts:
        print(f"❌ Error: No transcript files found in {transcripts_dir}")
        return None
    
    # Sort by size (smaller files = faster for demo)
    transcripts.sort(key=lambda f: f.stat().st_size)
    
    print("📁 Available test transcripts:")
    print()
    
    for i, f in enumerate(transcripts, 1):
        size_kb = f.stat().st_size / 1024
        print(f"  {i}. {f.name}")
        print(f"     Size: {size_kb:.1f} KB")
        print()
    
    print("=" * 80)
    print()
    
    # Auto-select smallest for demo
    selected = transcripts[0]
    print(f"✅ Auto-selected: {selected.name} (smallest file for faster demo)")
    print()
    print("💡 Tip: To process a different file, edit demo_langfuse_pipeline.py")
    print()
    
    return selected


def explain_pipeline():
    """Explain what will happen"""
    print("=" * 80)
    print("  📚 PIPELINE OVERVIEW")
    print("=" * 80)
    print()
    print("The pipeline will execute these agents in sequence:")
    print()
    print("  1. 🔤 Structuring Agent - Semantic NLP analysis")
    print("  2. 📄 Parser Agent - Extract header and parse dialogue")
    print("  3. ✂️  Chunker Agent - Split into semantic chunks")
    print("  4. 🧠 Embedder Agent - Generate vector embeddings")
    print("  5. 📧 Email Agent - Draft follow-up email")
    print("  6. 📱 Social Agent - Create social media content")
    print("  7. 🏆 Sales Coach Agent - Provide coaching feedback")
    print("  8. 💼 CRM Agent - Consolidate all data")
    print("  9. 💾 Persistence Agent - Save to databases")
    print()
    print("Each agent's execution will be traced in LangFuse with:")
    print("  - Execution time")
    print("  - Input/output data")
    print("  - Performance metrics")
    print("  - Any errors or warnings")
    print()
    print("=" * 80)
    print()


async def run_demo():
    """Run the demo pipeline"""
    # Print banner
    print_banner()
    
    # Check LangFuse is configured
    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        print("❌ ERROR: LangFuse not configured")
        print()
        print("Please set up LangFuse first:")
        print("  1. Start LangFuse: docker-compose -f docker-compose.langfuse.yml up -d")
        print("  2. Create API keys at: http://localhost:3000/settings/api-keys")
        print("  3. Add keys to .env file")
        print()
        print("See: docs/LANGFUSE_SETUP.md for detailed instructions")
        return False
    
    print(f"✅ LangFuse configured")
    print(f"   Host: {settings.LANGFUSE_HOST}")
    print(f"   Public Key: {settings.LANGFUSE_PUBLIC_KEY[:20]}...")
    print()
    
    # Select test file
    test_file = select_test_file()
    if not test_file:
        return False
    
    # Explain pipeline
    explain_pipeline()
    
    # Confirm start
    print("Press Enter to start the pipeline demo (or Ctrl+C to cancel)...")
    try:
        input()
    except KeyboardInterrupt:
        print()
        print("Demo cancelled by user")
        return False
    
    print()
    print("=" * 80)
    print(f"  🚀 STARTING PIPELINE")
    print("=" * 80)
    print(f"📄 File: {test_file.name}")
    print(f"📏 Size: {test_file.stat().st_size / 1024:.1f} KB")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Import and run enhanced pipeline
    try:
        from orchestrator.pipeline_langfuse_enhanced import run_pipeline
        
        start_time = datetime.now()
        
        # Run the pipeline
        result = await run_pipeline(test_file)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result:
            print()
            print("=" * 80)
            print("  ✅ PIPELINE COMPLETED SUCCESSFULLY")
            print("=" * 80)
            print()
            print(f"⏱️  Duration: {duration:.1f} seconds")
            print()
            
            # Show key results
            if result.get("transcript_id"):
                print(f"📋 Transcript ID: {result['transcript_id']}")
            
            if result.get("crm_data"):
                crm = result["crm_data"]
                if isinstance(crm, dict):
                    print(f"👤 Client: {crm.get('client_name', 'Unknown')}")
                    print(f"💰 Deal Amount: ${crm.get('deal', 0)}")
                    print(f"📊 Outcome: {crm.get('outcome', 'Unknown')}")
            
            print()
            print("=" * 80)
            print("  🔍 VIEW RESULTS IN LANGFUSE")
            print("=" * 80)
            print()
            print(f"1. Open LangFuse UI: {settings.LANGFUSE_HOST}")
            print()
            print("2. Navigate to Traces:")
            print(f"   {settings.LANGFUSE_HOST}/traces")
            print()
            print("3. Find your trace (should be at the top):")
            print(f"   Look for: 'Pipeline: {test_file.name}'")
            print()
            print("4. Click on the trace to see:")
            print("   - Complete timeline of agent executions")
            print("   - Timing for each agent")
            print("   - Input/output data")
            print("   - LLM generations")
            print("   - Performance metrics")
            print()
            print("=" * 80)
            print()
            
            # Provide learning resources
            print("📚 LEARN MORE")
            print()
            print("To understand what you're seeing in LangFuse:")
            print("  - Read: docs/LANGFUSE_USAGE_GUIDE.md")
            print("  - Learn how to interpret traces")
            print("  - Find performance bottlenecks")
            print("  - Debug pipeline issues")
            print()
            
            return True
            
        else:
            print()
            print("=" * 80)
            print("  ❌ PIPELINE FAILED")
            print("=" * 80)
            print()
            print("Check the error messages above for details.")
            print()
            print("The error was logged to LangFuse.")
            print(f"View at: {settings.LANGFUSE_HOST}/traces")
            print()
            print("For troubleshooting help:")
            print("  - See: docs/LANGFUSE_TROUBLESHOOTING.md")
            print()
            return False
            
    except ImportError as e:
        print()
        print(f"❌ Import error: {e}")
        print()
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        print()
        return False
    
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 80)
        print("  ⚠️  PIPELINE INTERRUPTED BY USER")
        print("=" * 80)
        print()
        print("The partial trace is still available in LangFuse.")
        print(f"View at: {settings.LANGFUSE_HOST}/traces")
        print()
        return False
    
    except Exception as e:
        print()
        print("=" * 80)
        print(f"  ❌ UNEXPECTED ERROR")
        print("=" * 80)
        print()
        print(f"Error: {type(e).__name__}: {e}")
        print()
        
        import traceback
        print("Stack trace:")
        traceback.print_exc()
        print()
        
        print("For help:")
        print("  - See: docs/LANGFUSE_TROUBLESHOOTING.md")
        print()
        return False


def print_tips():
    """Print helpful tips"""
    print("=" * 80)
    print("  💡 TIPS FOR SUCCESS")
    print("=" * 80)
    print()
    print("1. Keep LangFuse UI open while pipeline runs")
    print("   - Refresh the Traces page to see updates in real-time")
    print()
    print("2. Compare multiple runs")
    print("   - Run the demo again with a different transcript")
    print("   - Compare execution times in LangFuse")
    print()
    print("3. Experiment with filters")
    print("   - Filter by date, status, or transcript name")
    print("   - Search for specific clients or error types")
    print()
    print("4. Deep dive into agents")
    print("   - Click on any agent in the timeline")
    print("   - See exact inputs, outputs, and timing")
    print()
    print("5. Monitor for issues")
    print("   - Red bars = errors")
    print("   - Long bars = potential bottlenecks")
    print("   - Check LLM token usage")
    print()
    print("=" * 80)
    print()


def main():
    """Main entry point"""
    try:
        # Run the demo
        success = asyncio.run(run_demo())
        
        # Print tips
        print_tips()
        
        # Final message
        if success:
            print()
            print("🎉 Demo completed successfully!")
            print()
            print("Next steps:")
            print("  1. Explore the trace in LangFuse UI")
            print("  2. Read the usage guide: docs/LANGFUSE_USAGE_GUIDE.md")
            print("  3. Try processing your own transcripts")
            print()
            print("To run the enhanced pipeline on any transcript:")
            print("  python orchestrator/pipeline_langfuse_enhanced.py")
            print()
            sys.exit(0)
        else:
            print()
            print("⚠️  Demo encountered issues")
            print()
            print("Troubleshooting:")
            print("  - Check logs above for specific errors")
            print("  - Run: python scripts/test_langfuse_complete.py")
            print("  - See: docs/LANGFUSE_TROUBLESHOOTING.md")
            print()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print()
        print()
        print("Demo cancelled by user")
        print()
        sys.exit(130)


if __name__ == "__main__":
    main()


