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
        # Pattern 1: [00:15:32] Speaker Name: Text...
        self.bracketed_pattern = re.compile(r'\[(.*?)\]\s+([^:]+):\s+(.*)')
        # Pattern 2: 00:15:32 - Speaker Name (text follows on next lines, may have leading spaces)
        self.dashed_pattern = re.compile(r'^\s*(\d{2}:\d{2}:\d{2})\s+-\s+(.+)$')

    def _get_semantic_metadata_for_timestamp(self, timestamp: str, semantic_turns: list) -> Dict[str, Any]:
        """
        Retrieves semantic metadata for a specific timestamp from NLP analysis.

        Args:
            timestamp: Dialogue turn timestamp (HH:MM:SS)
            semantic_turns: List of semantic turn metadata from NLP analysis

        Returns:
            Dictionary with {intent, sentiment, discourse_marker, contains_entity} or empty dict
        """
        if not semantic_turns:
            return {}

        # Find matching semantic turn by timestamp
        for st in semantic_turns:
            if st.get("timestamp") == timestamp:
                return {
                    "intent": st.get("intent"),
                    "sentiment": st.get("sentiment"),
                    "discourse_marker": st.get("discourse_marker"),
                    "contains_entity": st.get("contains_entity")
                }

        return {}

    def _get_phase_for_timestamp(self, timestamp: str, conversation_phases: list) -> str:
        """
        Determines which conversation phase a dialogue turn belongs to based on timestamp.

        Args:
            timestamp: Dialogue turn timestamp (HH:MM:SS)
            conversation_phases: List of {"phase": str, "start_timestamp": str}

        Returns:
            Phase name string (e.g., "client's estate details")
        """
        if not conversation_phases:
            return "unknown"

        # Filter out phases without start_timestamp (defensive coding)
        valid_phases = [p for p in conversation_phases if p.get("start_timestamp")]
        if not valid_phases:
            # If no phases have timestamps, just return the first phase name
            return conversation_phases[0].get("phase", "unknown")

        # Sort phases by timestamp
        sorted_phases = sorted(valid_phases, key=lambda p: p["start_timestamp"])

        # Convert timestamp to seconds for comparison
        def time_to_seconds(time_str):
            parts = time_str.split(':')
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

        current_seconds = time_to_seconds(timestamp)

        # Find the phase this timestamp belongs to
        current_phase = sorted_phases[0]["phase"]  # Default to first phase
        for phase in sorted_phases:
            phase_seconds = time_to_seconds(phase["start_timestamp"])
            if current_seconds >= phase_seconds:
                current_phase = phase["phase"]
            else:
                break

        return current_phase

    def _extract_transcript_id(self, content: str) -> str:
        """
        Extracts the transcript_id from the file header.

        Line 1:  Meeting Title
        Line 2:  (blank)
        Line 3:  Client Name
        Line 4:  (blank)
        Line 5:  Email
        Line 6:  (blank)
        Line 7:  Date (ISO 8601)
        Line 8:  (blank)
        Line 9:  Transcript ID
        Line 10: (blank)
        Line 11: URL
        Line 12: (blank)
        Line 13: Duration (decimal minutes)
        Line 14: (blank)
        Line 15: First dialogue turn

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

    async def run(self, file_path: Path, conversation_phases: list = None, semantic_turns: list = None) -> Dict[str, Any]:
        """
        Parses the transcript and enriches dialogue turns with metadata.

        NEW ARCHITECTURE: Receives conversation_phases + semantic_turns from StructuringAgent NLP analysis
        to enrich each dialogue turn with phase + semantic metadata (intent, sentiment, discourse).

        Supports two formats:
        1. [00:15:32] Speaker Name: Text...
        2. 00:15:32 - Speaker Name
              Text continues on next lines...

        Args:
            file_path: Path to transcript file
            conversation_phases: List of {"phase": str, "start_timestamp": str} from StructuringAgent
            semantic_turns: List of {"timestamp": str, "intent": str, "sentiment": str, ...} from NLP analysis

        Returns:
            Dictionary containing:
            - structured_dialogue: List of parsed dialogue turns (enriched with phase + semantic metadata)
            - transcript_id: The extracted or generated transcript ID
            - conversation_phases: Passthrough for downstream agents
        """
        print(f"📜 ParserAgent: Parsing transcript {file_path.name}...")
        if conversation_phases:
            print(f"   📊 Enriching dialogue with {len(conversation_phases)} conversation phases")
        if semantic_turns:
            print(f"   🧠 Enriching with semantic NLP metadata from {len(semantic_turns)} analyzed turns")
        structured_dialogue = []
        transcript_id = None

        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract transcript_id from header
            transcript_id = self._extract_transcript_id(content)

            lines = content.strip().split('\n')

            # Try bracketed format first
            for line in lines:
                match = self.bracketed_pattern.match(line)
                if match:
                    timestamp, speaker, text = match.groups()
                    turn = {
                        "timestamp": timestamp.strip(),
                        "speaker": speaker.strip(),
                        "text": text.strip()
                    }
                    # Enrich with conversation phase if available
                    if conversation_phases:
                        turn["conversation_phase"] = self._get_phase_for_timestamp(timestamp.strip(), conversation_phases)

                    # Enrich with semantic NLP metadata if available
                    if semantic_turns:
                        semantic_meta = self._get_semantic_metadata_for_timestamp(timestamp.strip(), semantic_turns)
                        turn.update(semantic_meta)  # Add intent, sentiment, discourse_marker, contains_entity

                    structured_dialogue.append(turn)

            # If no bracketed format found, try dashed format with multiline text
            if not structured_dialogue:
                i = 0
                while i < len(lines):
                    line = lines[i]
                    match = self.dashed_pattern.match(line)  # Don't strip - pattern handles spaces
                    if match:
                        timestamp, speaker = match.groups()
                        # Collect text from following indented lines until next timestamp or non-indented line
                        text_lines = []
                        i += 1
                        while i < len(lines):
                            next_line = lines[i]
                            # Stop if we hit another timestamp line
                            if self.dashed_pattern.match(next_line):
                                break
                            # Only collect lines that start with spaces (indented text)
                            if next_line.startswith('  ') and next_line.strip():
                                text_lines.append(next_line.strip())
                            i += 1

                        if text_lines:
                            turn = {
                                "timestamp": timestamp.strip(),
                                "speaker": speaker.strip(),
                                "text": '    '.join(text_lines)  # Join with spaces
                            }
                            # Enrich with conversation phase if available
                            if conversation_phases:
                                turn["conversation_phase"] = self._get_phase_for_timestamp(timestamp.strip(), conversation_phases)

                            # Enrich with semantic NLP metadata if available
                            if semantic_turns:
                                semantic_meta = self._get_semantic_metadata_for_timestamp(timestamp.strip(), semantic_turns)
                                turn.update(semantic_meta)  # Add intent, sentiment, discourse_marker, contains_entity

                            structured_dialogue.append(turn)
                        continue
                    i += 1

            print(
                f"   Successfully parsed {len(structured_dialogue)} dialogue turns.")
            if conversation_phases:
                print(f"   ✅ Enriched all turns with conversation phase metadata")

            return {
                "structured_dialogue": structured_dialogue,
                "transcript_id": transcript_id,
                "conversation_phases": conversation_phases  # Pass through for downstream agents
            }

        except Exception as e:
            print(
                f"   ❌ ERROR: An unexpected error occurred during parsing: {e}")
            return {
                "structured_dialogue": [],
                "transcript_id": None
            }
