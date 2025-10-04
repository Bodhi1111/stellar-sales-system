import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from agents.base_agent import BaseAgent
from config.settings import Settings, settings

class ParserAgent(BaseAgent):
    """
    Parses a raw transcript into a structured format of dialogue turns.
    Also extracts the transcript_id from the file header for use across the system.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        # This "regular expression" is a pattern to find and capture
        # the timestamp, speaker, and text from each line.
        # It expects a format like: [00:15:32] Speaker Name: Text...
        self.line_pattern = re.compile(r'\[(.*?)\]\s+([^:]+):\s+(.*)')

    def _extract_transcript_id(self, content: str) -> str:
        """
        Extracts the transcript_id from the file header.

        Expected header format:
        Line 1: Title (e.g., "Bhaskar DasGupta: Estate Planning Advisor Meeting")
        Line 2: Name
        Line 3: Email
        Line 4: Datetime (ISO format, e.g., "2025-10-03T20:00:00Z")
        Line 5: transcript_id (numeric, e.g., "61552532")
        Line 6: URL (e.g., "https://fathom.video/calls/...")

        Returns:
            The transcript_id as a string, or a generated ID if not found
        """
        lines = content.split('\n')

        # Look for a purely numeric line in the header (first 10 lines)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            # Look for a line that's purely numeric and reasonably long (6+ digits)
            if line.isdigit() and len(line) >= 6:
                print(f"   Found transcript_id in header: {line}")
                return line

        # Fallback: generate from filename if not found
        print("   ⚠️ Warning: Could not find transcript_id in header, generating from filename")
        import hashlib
        fallback_id = hashlib.md5(lines[0].encode()).hexdigest()[:12]
        return fallback_id

    async def run(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses the transcript and extracts the transcript_id.

        Returns:
            Dictionary containing:
            - structured_dialogue: List of parsed dialogue turns
            - transcript_id: The extracted or generated transcript ID
        """
        print(f"📜 ParserAgent received file: {file_path.name}")
        structured_dialogue = []
        transcript_id = None

        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract transcript_id from header
            transcript_id = self._extract_transcript_id(content)

            lines = content.strip().split('\n')

            for line in lines:
                match = self.line_pattern.match(line)
                if match:
                    timestamp, speaker, text = match.groups()
                    structured_dialogue.append({
                        "timestamp": timestamp.strip(),
                        "speaker": speaker.strip(),
                        "text": text.strip()
                    })

            print(f"   Successfully parsed {len(structured_dialogue)} dialogue turns.")
            return {
                "structured_dialogue": structured_dialogue,
                "transcript_id": transcript_id
            }

        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred during parsing: {e}")
            return {
                "structured_dialogue": [],
                "transcript_id": None
            }