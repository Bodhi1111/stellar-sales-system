#!/usr/bin/env python3
"""Simple test - just process one small transcript and show results"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.parser.parser_agent import ParserAgent
from config.settings import settings

async def test_parser():
    """Test just the parser on a small file"""
    test_file = Path("data/transcripts/test_sprint01.txt")

    print(f"\n{'='*60}")
    print("SIMPLE PARSER TEST")
    print(f"{'='*60}")
    print(f"File: {test_file.name}")
    print(f"Size: {test_file.stat().st_size} bytes\n")

    # Initialize parser
    parser = ParserAgent(settings)

    # Run parser
    print("Running parser...")
    result = await parser.run(
        file_path=test_file,
        conversation_phases=None,
        semantic_turns=None
    )

    # Show results
    print(f"\n✅ PARSER RESULTS:")
    print(f"   Transcript ID: {result.get('transcript_id')}")
    print(f"   Dialogue turns: {len(result.get('structured_dialogue', []))}")

    header = result.get('header_metadata', {})
    print(f"\n📋 HEADER METADATA:")
    print(f"   Client: {header.get('client_name')}")
    print(f"   Email: {header.get('client_email')}")
    print(f"   Date: {header.get('meeting_date')}")
    print(f"   Duration: {header.get('duration_minutes')} min")

    print(f"\n🗣️  DIALOGUE SAMPLE (first 3 turns):")
    for i, turn in enumerate(result.get('structured_dialogue', [])[:3]):
        print(f"   [{turn.get('timestamp')}] {turn.get('speaker_name')}: {turn.get('text')[:60]}...")

    print(f"\n{'='*60}\n")
    return result

if __name__ == "__main__":
    asyncio.run(test_parser())
