#!/usr/bin/env python3
"""
Quick test to verify parser extracts header metadata correctly for Yongsik Johng transcript.
"""
from pathlib import Path
from agents.parser.parser_agent import ParserAgent
from config.settings import settings

async def test_parser():
    """Test parser header extraction only."""
    parser = ParserAgent(settings)

    file_path = Path("/Users/joshuavaughan/dev/Projects/stellar-sales-system/data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt")

    print(f"\n{'='*80}")
    print(f"Testing Parser on: {file_path.name}")
    print(f"{'='*80}\n")

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Show first 20 lines
    lines = raw_text.split('\n')[:20]
    print("First 20 lines of transcript:")
    for i, line in enumerate(lines):
        print(f"Line {i:2d}: [{repr(line)}]")

    print("\n" + "="*80)
    print("Extracting Header Metadata...")
    print("="*80 + "\n")

    # Extract header metadata
    metadata = parser._extract_header_metadata(raw_text)

    # Print results
    for key, value in metadata.items():
        print(f"{key:20s}: {value}")

    print("\n" + "="*80)
    print("Validation:")
    print("="*80)

    # Validation checks
    checks = {
        'meeting_title': metadata.get('meeting_title') is not None,
        'client_name': metadata.get('client_name') == 'YONGSIK JOHNG',
        'client_email': metadata.get('client_email') == 'yjohng@yahoo.com',
        'meeting_date': metadata.get('meeting_date') == '2025-07-16',
        'meeting_url': metadata.get('meeting_url') is not None and 'http' in str(metadata.get('meeting_url')),
        'duration_minutes': metadata.get('duration_minutes') is not None
    }

    for field, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {field}: {metadata.get(field)}")

    all_passed = all(checks.values())
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
    else:
        print("❌ SOME CHECKS FAILED")
    print("="*80 + "\n")

    return metadata

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_parser())
