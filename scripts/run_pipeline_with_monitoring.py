#!/usr/bin/env python3
"""
Run the ingestion pipeline with detailed monitoring and progress updates.
This provides visibility into the pipeline execution similar to N8N.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.graph import app
from config.settings import settings


class PipelineMonitor:
    """Monitor and display pipeline progress"""

    def __init__(self):
        self.start_time = None
        self.node_times = {}

    def print_header(self, file_path: Path):
        """Print pipeline header"""
        print("\n" + "="*80)
        print(f"🚀 STELLAR SALES SYSTEM - Ingestion Pipeline")
        print("="*80)
        print(f"📄 File: {file_path.name}")
        print(f"📊 Size: {file_path.stat().st_size / 1024:.1f} KB")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

    def print_node_start(self, node_name: str):
        """Print node execution start"""
        self.node_times[node_name] = datetime.now()
        icon = self._get_node_icon(node_name)
        print(f"\n{icon} {node_name.upper()}")
        print(f"   ⏱️  Started at {self.node_times[node_name].strftime('%H:%M:%S')}")
        print(f"   " + "-"*70)

    def print_node_complete(self, node_name: str, state_update: dict):
        """Print node completion with key outputs"""
        if node_name in self.node_times:
            elapsed = (datetime.now() - self.node_times[node_name]).total_seconds()
            print(f"   " + "-"*70)
            print(f"   ✅ Completed in {elapsed:.2f}s")

            # Print key outputs based on node type
            self._print_node_outputs(node_name, state_update)
            print()

    def print_summary(self, final_state: dict):
        """Print pipeline summary"""
        total_time = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "="*80)
        print("📊 PIPELINE SUMMARY")
        print("="*80)
        print(f"⏱️  Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        print(f"📝 Transcript ID: {final_state.get('transcript_id', 'N/A')}")

        # Chunk statistics
        chunks_data = final_state.get('chunks_data', {})
        if chunks_data:
            print(f"\n📦 Chunks Created:")
            print(f"   - Child chunks: {len(chunks_data.get('child_chunks', []))}")
            print(f"   - Parent chunks: {len(chunks_data.get('parent_chunks', []))}")
            print(f"   - Total chunks: {len(chunks_data.get('all_chunks', []))}")

        # Database status
        db_status = final_state.get('db_save_status', {})
        if db_status:
            print(f"\n💾 Database Status:")
            print(f"   - PostgreSQL: {'✅' if db_status.get('postgres_saved') else '❌'}")
            print(f"   - Baserow: {'✅' if db_status.get('baserow_synced') else '❌'}")

        print("\n" + "="*80)
        print("✨ Pipeline completed successfully!")
        print("="*80 + "\n")

    def _get_node_icon(self, node_name: str) -> str:
        """Get emoji icon for node type"""
        icons = {
            'structuring': '🧠',
            'parser': '📋',
            'chunker': '✂️',
            'embedder': '🔢',
            'email': '✉️',
            'social': '📱',
            'sales_coach': '🎯',
            'crm': '💼',
            'persistence': '💾'
        }
        return icons.get(node_name, '⚙️')

    def _print_node_outputs(self, node_name: str, state: dict):
        """Print relevant outputs for each node"""
        if node_name == 'parser':
            dialogue = state.get('structured_dialogue', [])
            print(f"   📊 Extracted {len(dialogue)} speaker turns")
            header = state.get('header_metadata', {})
            if header:
                print(f"   👤 Client: {header.get('client_name', 'Unknown')}")
                print(f"   📧 Email: {header.get('client_email', 'Unknown')}")

        elif node_name == 'structuring':
            phases = state.get('conversation_phases', [])
            if phases:
                print(f"   🗣️  Identified {len(phases)} conversation phases")

        elif node_name == 'chunker':
            chunks_data = state.get('chunks_data', {})
            child_count = len(chunks_data.get('child_chunks', []))
            parent_count = len(chunks_data.get('parent_chunks', []))
            print(f"   📦 Created {child_count} child + {parent_count} parent chunks")

        elif node_name == 'embedder':
            print(f"   🔢 Vectors stored in Qdrant")
            print(f"   🌐 View at: http://localhost:6333/dashboard")

        elif node_name == 'crm':
            crm_data = state.get('crm_data', {})
            if crm_data:
                print(f"   💼 CRM record prepared")
                if 'estate_value' in crm_data and crm_data['estate_value']:
                    print(f"   💰 Estate Value: ${crm_data['estate_value']:,.0f}")

        elif node_name == 'persistence':
            print(f"   💾 Data persisted to PostgreSQL + Baserow")
            print(f"   🌐 View CRM: http://localhost:8080")


async def run_pipeline_with_monitoring(file_path: Path):
    """Run pipeline with detailed monitoring"""
    monitor = PipelineMonitor()
    monitor.start_time = datetime.now()
    monitor.print_header(file_path)

    try:
        # Read the raw text from the file
        raw_text = file_path.read_text(encoding='utf-8')

        # Initial state
        initial_state = {"file_path": file_path, "raw_text": raw_text}

        # Run the graph with monitoring
        final_state = None
        async for event in app.astream(initial_state):
            for node_name, state_update in event.items():
                monitor.print_node_start(node_name)

                # Simulate brief pause to show progress
                await asyncio.sleep(0.1)

                # Update final state
                if final_state is None:
                    final_state = state_update.copy() if state_update else {}
                else:
                    if state_update:
                        final_state.update(state_update)

                monitor.print_node_complete(node_name, final_state)

        # Print summary
        if final_state:
            monitor.print_summary(final_state)

        return final_state

    except Exception as e:
        print(f"\n❌ ERROR: Pipeline failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Use small test transcript (YONGSIK JOHNG is too large for Mistral's 4K context window)
    test_file = Path("data/transcripts/test_sprint01.txt")

    if not test_file.exists():
        print(f"❌ ERROR: File not found: {test_file}")
        print(f"   Please ensure the transcript exists at {test_file}")
        sys.exit(1)

    print("⚠️  Note: Using small test transcript due to Mistral 4K context limit")
    print("   For large transcripts (60KB+), use DeepSeek 33B with 16K context\n")

    asyncio.run(run_pipeline_with_monitoring(test_file))
