import re
from pathlib import Path
from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from config.settings import Settings, settings

class ParserAgent(BaseAgent):
    """
    Parses a raw transcript into a structured format of dialogue turns.
    """
    def __init__(self, settings: Settings):
        super().__init__(settings)
        # This "regular expression" is a pattern to find and capture
        # the timestamp, speaker, and text from each line.
        # It expects a format like: [00:15:32] Speaker Name: Text...
        self.line_pattern = re.compile(r'\[(.*?)\]\s+([^:]+):\s+(.*)')

    async def run(self, file_path: Path) -> List[Dict[str, Any]]:
        print(f"📜 ParserAgent received file: {file_path.name}")
        structured_dialogue = []
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.strip().split('\\n')

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
            return structured_dialogue

        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred during parsing: {e}")
            return []