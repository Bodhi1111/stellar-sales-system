"""
Quick test of the simplified pipeline.
"""

import asyncio
from pathlib import Path
from simple_pipeline import SimplePipeline


async def test():
    """Test with one of your existing transcripts."""
    
    # Find a test transcript
    test_files = [
        "data/transcripts/NELSON DIAZ: Estate Planning Advisor Meeting .txt",
        "data/transcripts/YONGSIK JOHNG: Estate Planning Advisor Meeting.txt",
        "data/transcripts/Robin Michalek: Estate Planning Advisor Meeting .txt",
    ]
    
    for file_path_str in test_files:
        file_path = Path(file_path_str)
        if file_path.exists():
            print(f"✅ Found test file: {file_path.name}")
            
            pipeline = SimplePipeline()
            result = await pipeline.process_transcript(file_path)
            
            print("\n🎯 QUICK SUMMARY:")
            print(f"   File: {result['file']}")
            print(f"   Client: {result['crm_data'].get('client_name')}")
            print(f"   Outcome: {result['crm_data'].get('outcome')}")
            print(f"   Baserow: {result['baserow_status']}")
            
            return  # Just test one file
    
    print("❌ No test files found. Please specify a transcript file.")
    print("\nAvailable transcripts:")
    transcript_dir = Path("data/transcripts")
    if transcript_dir.exists():
        for f in transcript_dir.glob("*.txt"):
            print(f"   - {f}")


if __name__ == "__main__":
    asyncio.run(test())

