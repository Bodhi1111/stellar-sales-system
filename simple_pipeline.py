"""
SIMPLIFIED PIPELINE - No agents, no orchestration, just results.

This script replaces the entire multi-agent system with a single,
easy-to-debug workflow:
1. Read transcript
2. Extract CRM data with ONE Claude API call
3. Save to Baserow

When something breaks, you know exactly where.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from config.settings import Settings
from core.database.baserow import BaserowManager
from core.llm_client import LLMClient


class SimplePipeline:
    """One script to rule them all."""
    
    def __init__(self):
        self.settings = Settings()
        self.llm = LLMClient(self.settings, timeout=180)  # 3 min timeout for extraction
        self.baserow = BaserowManager(self.settings)
    
    async def process_transcript(self, file_path: Path) -> Dict[str, Any]:
        """Process transcript and sync to Baserow."""
        print(f"\n🚀 Processing: {file_path.name}")
        print("=" * 60)
        
        # Step 1: Read transcript
        print("\n📖 Step 1: Reading transcript...")
        transcript_text = file_path.read_text(encoding='utf-8')
        print(f"   ✅ Read {len(transcript_text)} characters")
        
        # Step 2: Extract ALL CRM data in ONE API call
        print("\n🤖 Step 2: Extracting CRM data with Claude...")
        crm_data = await self._extract_crm_data(transcript_text)
        print(f"   ✅ Extracted data for: {crm_data.get('client_name', 'Unknown')}")
        
        # Step 3: Sync to Baserow
        print("\n💾 Step 3: Syncing to Baserow...")
        transcript_id = crm_data.get('transcript_id', str(hash(file_path.name)))
        result = await self.baserow.sync_crm_data(crm_data, transcript_id)
        
        if result['status'] == 'success':
            print(f"   ✅ Synced to Baserow (external_id: {result['external_id']})")
        else:
            print(f"   ❌ Sync failed: {result.get('error')}")
        
        print("\n" + "=" * 60)
        print("✨ Pipeline Complete!\n")
        
        return {
            'file': file_path.name,
            'crm_data': crm_data,
            'baserow_status': result['status']
        }
    
    async def _extract_crm_data(self, transcript: str) -> Dict[str, Any]:
        """
        Single Claude API call to extract ALL CRM data.
        
        This replaces: ParserAgent, ExtractorAgent, CRMAgent, ChunkerAgent
        """
        
        prompt = f"""You are a sales CRM data extraction expert. Extract ALL relevant information from this sales transcript.

TRANSCRIPT:
{transcript}

Extract the following in JSON format:

{{
    "transcript_id": "unique ID from header or filename",
    "client_name": "full name",
    "client_email": "email address",
    "meeting_date": "YYYY-MM-DD",
    "meeting_time": "HH:MM",
    "meeting_title": "brief title",
    "duration_minutes": 30,
    "marital_status": "Single/Married/Divorced/Widowed",
    "children_count": 0,
    "estate_value": 0,
    "real_estate_count": 0,
    "product_discussed": "Estate Planning, Trust, LLC, etc",
    "deal": 12000,
    "deposit": 1500,
    "outcome": "Won/Lost/Follow-up Scheduled",
    "win_probability": 0.8,
    "close_date": "YYYY-MM-DD if won",
    "objections_raised": "list of objections",
    "action_items": "next steps",
    "transcript_summary": "brief summary of conversation",
    "follow_up_email_draft": "draft email text",
    "social_media_quote": "testimonial or quote for social",
    "coaching_opportunities": "feedback for sales rep"
}}

Rules:
- Use actual values from transcript
- Set numeric fields to 0 if not mentioned
- Set text fields to empty string if not found
- Be precise with dates (YYYY-MM-DD format)
- For outcome: only use "Won", "Lost", or "Follow-up Scheduled"
"""
        
        try:
            # Use your existing LLM client with JSON formatting
            result = self.llm.generate_json(prompt, timeout=180)
            
            if result["success"]:
                print(f"   ✅ Extraction completed in {result['elapsed_time']:.1f}s")
                return result["data"]
            else:
                print(f"   ❌ Extraction failed: {result.get('error')}")
                # Return minimal data structure
                return {
                    "transcript_id": "unknown",
                    "client_name": "Unknown",
                    "outcome": "Pending"
                }
            
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            # Return minimal data structure
            return {
                "transcript_id": "unknown",
                "client_name": "Unknown",
                "outcome": "Pending"
            }


# Command-line interface
async def main():
    """Run the simplified pipeline on a transcript file."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_pipeline.py <transcript_file>")
        print("\nExample:")
        print("  python simple_pipeline.py data/transcripts/john_doe.txt")
        return
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    pipeline = SimplePipeline()
    result = await pipeline.process_transcript(file_path)
    
    print("\n📊 RESULT:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

