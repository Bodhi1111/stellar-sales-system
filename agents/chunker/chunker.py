import sys
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter

from agents.base_agent import BaseAgent
from config.settings import settings
from core.semantic_chunker import SemanticDialogueChunker


class ChunkerAgent(BaseAgent):
    """
    This agent takes a file path, reads the text, and splits it into chunks.
    """

    def __init__(self, settings):
        super().__init__(settings)
        # Initialize BOTH chunkers for hybrid approach

        # 1. Semantic Dialogue Chunker (PRIMARY - for dialogue sections)
        #    Respects turn boundaries, conversation phases, entity preservation
        self.semantic_chunker = SemanticDialogueChunker(
            target_chunk_size=1400,  # ~350 tokens, optimal for embedding coherence
            min_chunk_size=700,      # 50% of target
            max_chunk_size=2100,     # 150% of target
            overlap_turns=2          # 2 dialogue turns overlap for context
        )

        # 2. Character-based splitter (FALLBACK - for non-dialogue sections like headers)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1400,     # ~350 tokens
            chunk_overlap=140,   # 10% overlap
        )

    def _extract_chunk_metadata(self, chunk_text: str, structured_dialogue: list = None) -> dict:
        """
        Extracts metadata for a chunk from the enriched structured dialogue.

        Determines the conversation phase, speakers, and timestamp range by analyzing
        which dialogue turns appear in this chunk.

        Args:
            chunk_text: The text content of the chunk
            structured_dialogue: List of enriched dialogue turns with conversation_phase

        Returns:
            dict with keys: phase, speakers, timestamp_start, timestamp_end
        """
        if not structured_dialogue:
            return {"phase": None, "speakers": [], "timestamp_start": None, "timestamp_end": None}

        # Find dialogue turns that appear in this chunk
        import re
        timestamp_pattern = re.compile(r'(\d{2}:\d{2}:\d{2})')
        timestamps_in_chunk = timestamp_pattern.findall(chunk_text)

        if not timestamps_in_chunk:
            return {"phase": None, "speakers": [], "timestamp_start": None, "timestamp_end": None}

        # Find matching dialogue turns
        matching_turns = []
        for turn in structured_dialogue:
            if turn.get("timestamp") in timestamps_in_chunk:
                matching_turns.append(turn)

        if not matching_turns:
            return {"phase": None, "speakers": [], "timestamp_start": None, "timestamp_end": None}

        # Extract metadata from matching turns
        phases = [turn.get("conversation_phase") for turn in matching_turns if turn.get("conversation_phase")]
        speakers = list(set(turn.get("speaker") for turn in matching_turns if turn.get("speaker")))

        # Use the most common phase in this chunk
        phase = max(set(phases), key=phases.count) if phases else None

        # SEMANTIC NLP METADATA EXTRACTION
        # Collect intent, sentiment, discourse markers from enriched turns
        intents = [turn.get("intent") for turn in matching_turns if turn.get("intent")]
        sentiments = [turn.get("sentiment") for turn in matching_turns if turn.get("sentiment")]
        discourse_markers = [turn.get("discourse_marker") for turn in matching_turns if turn.get("discourse_marker")]

        # Determine dominant metadata
        dominant_intent = max(set(intents), key=intents.count) if intents else None
        dominant_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else None
        has_entities = any(turn.get("contains_entity") for turn in matching_turns)

        return {
            "phase": phase,
            "speakers": speakers,
            "timestamp_start": matching_turns[0].get("timestamp") if matching_turns else None,
            "timestamp_end": matching_turns[-1].get("timestamp") if matching_turns else None,
            # Semantic NLP metadata
            "dominant_intent": dominant_intent,
            "dominant_sentiment": dominant_sentiment,
            "contains_entities": has_entities,
            "discourse_markers": list(set(dm for dm in discourse_markers if dm and dm != "none"))
        }

    async def run(self, file_path: Path, structured_dialogue: list = None):
        """
        Creates semantic chunks from transcript with rich metadata preservation.

        NEW ARCHITECTURE: Receives enriched dialogue from ParserAgent
        Each chunk inherits metadata from the dialogue turns it contains.

        Args:
            file_path: Path to transcript file
            structured_dialogue: Enriched dialogue turns with conversation_phase metadata

        Returns:
            List of chunk dictionaries with metadata
        """
        print(f"📦 ChunkerAgent: Creating semantic chunks...")
        try:
            content = file_path.read_text(encoding='utf-8')
            print(f"   Successfully read {len(content)} characters.")

            # CRITICAL: Extract header section separately (lines 1-8)
            # Transcript Anatomy:
            #   Line 1: Meeting Title
            #   Line 2: Client Name
            #   Line 3: Client Email
            #   Line 4: Meeting Date (ISO 8601)
            #   Line 5: Transcript ID (numeric)
            #   Line 6: Meeting URL
            #   Line 7: Duration (minutes as decimal)
            #   Line 8: (blank line separator)
            #   Lines 9+: Dialogue with timestamps

            lines = content.split('\n')
            header_lines = []
            dialogue_start_index = 0

            # Find where dialogue starts (first line with timestamp pattern HH:MM:SS)
            import re
            timestamp_pattern = re.compile(r'^\s*\d{2}:\d{2}:\d{2}')

            for i, line in enumerate(lines):
                if timestamp_pattern.match(line):
                    dialogue_start_index = i
                    break

            # Separate header from dialogue
            if dialogue_start_index > 0:
                header_text = '\n'.join(lines[:dialogue_start_index]).strip()
                dialogue_text = '\n'.join(lines[dialogue_start_index:]).strip()

                print(f"   📋 Extracted header section ({dialogue_start_index} lines)")
                print(f"   💬 Dialogue section starts at line {dialogue_start_index + 1}")

                # NEW: Create chunks with metadata dictionaries
                chunks = []

                # Chunk 0: Header with metadata
                chunks.append({
                    "text": header_text,
                    "chunk_type": "header",
                    "conversation_phase": None,  # Header has no phase
                    "speakers": []
                })

                # Chunks 1+: Dialogue chunks with SEMANTIC chunking
                if structured_dialogue and len(structured_dialogue) > 0:
                    # Use SEMANTIC DIALOGUE CHUNKER (respects turn boundaries, phases)
                    print(f"   🧠 Using semantic dialogue chunking on {len(structured_dialogue)} turns")

                    # Get conversation phases from state (if available)
                    conversation_phases = None
                    if structured_dialogue[0].get("conversation_phase"):
                        # Extract unique phases from dialogue
                        phases_seen = {}
                        for turn in structured_dialogue:
                            phase_name = turn.get("conversation_phase")
                            timestamp = turn.get("timestamp")
                            if phase_name and phase_name not in phases_seen:
                                phases_seen[phase_name] = timestamp

                        conversation_phases = [
                            {"phase": name, "start_timestamp": ts, "end_timestamp": None}
                            for name, ts in phases_seen.items()
                        ]

                    # Chunk dialogue into semantically coherent segments
                    dialogue_chunk_turns = self.semantic_chunker.chunk_dialogue(
                        structured_dialogue,
                        conversation_phases
                    )

                    print(f"   ✅ Created {len(dialogue_chunk_turns)} semantic chunks")

                    # Convert each chunk (list of turns) to formatted text + metadata
                    for turn_list in dialogue_chunk_turns:
                        # Convert turns to text
                        chunk_text = self.semantic_chunker.turns_to_text(turn_list, format="dialogue")

                        # Compute rich metadata from turns
                        chunk_metadata = self.semantic_chunker.compute_chunk_metadata(turn_list)

                        chunks.append({
                            "text": chunk_text,
                            "chunk_type": "dialogue",
                            **chunk_metadata  # Unpack all computed metadata
                        })

                elif dialogue_text:
                    # FALLBACK: No structured dialogue available, use character-based chunking
                    print(f"   ⚠️ No structured dialogue, using fallback character-based chunking")
                    dialogue_chunks = self.text_splitter.split_text(dialogue_text)

                    for i, chunk_text in enumerate(dialogue_chunks):
                        chunks.append({
                            "text": chunk_text,
                            "chunk_type": "dialogue",
                            "conversation_phase": None,
                            "speakers": []
                        })

                print(f"   Split into {len(chunks)} chunks (1 header + {len(chunks)-1} dialogue)")
                if structured_dialogue:
                    print(f"   ✅ Enriched chunks with conversation phase metadata")
                print(f"   Header chunk preview: '{chunks[0]['text'][:100]}...'")
            else:
                # Fallback: No clear header boundary, chunk normally
                print(f"   ⚠️ No timestamp pattern found, chunking entire content")
                text_chunks = self.text_splitter.split_text(content)
                chunks = [{"text": chunk, "chunk_type": "unknown", "conversation_phase": None, "speakers": []}
                          for chunk in text_chunks]
                print(f"   Split text into {len(chunks)} chunks.")

            if chunks and len(chunks) > 0:
                print(f"   First chunk: '{chunks[0]['text'][:80]}...'")

            return chunks

        except FileNotFoundError:
            print(f"   ❌ ERROR: File not found at {file_path}")
        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred: {e}")


# This block allows us to test the agent by running the file directly
if __name__ == "__main__":
    import asyncio
    if len(sys.argv) > 1:
        file_to_chunk = Path(sys.argv[1])

        async def main():
            agent = ChunkerAgent(settings)
            await agent.run(file_path=file_to_chunk)
        asyncio.run(main())
    else:
        print("Usage: python agents/chunker/chunker.py <path_to_file>")
