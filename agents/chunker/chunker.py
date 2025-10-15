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

        # Parent-Child Semantic Dialogue Chunker
        # Creates speaker-turn child chunks + conversation-phase parent chunks
        self.semantic_chunker = SemanticDialogueChunker(
            turns_per_parent=7,        # Target 7 turns per parent chunk
            min_turns_per_parent=5,    # Minimum 5 turns before new parent
            max_turns_per_parent=10    # Maximum 10 turns before forced split
        )

    async def run(self, file_path: Path, structured_dialogue: list = None, transcript_id: str = None, conversation_phases: list = None):
        """
        Creates parent-child chunk hierarchy from transcript.

        PARENT-CHILD ARCHITECTURE:
        - Child chunks: Individual speaker turns (1 turn = 1 chunk, embedded)
        - Parent chunks: Conversation phase segments (5-10 turns, stored for context)
        - All chunks have UUIDs and rich metadata for Baserow/Qdrant storage

        Args:
            file_path: Path to transcript file
            structured_dialogue: Enriched dialogue turns with conversation_phase metadata
            transcript_id: External ID from header for linking
            conversation_phases: List of conversation phase boundaries

        Returns:
            Dict with:
                - all_chunks: Combined list of child + parent chunks (for Baserow sync)
                - child_chunks: Speaker-turn chunks (for embedding in Qdrant)
                - parent_chunks: Phase segment chunks (for context storage)
        """
        print(f"📦 ChunkerAgent: Creating parent-child chunk hierarchy...")
        try:
            content = file_path.read_text(encoding='utf-8')
            print(f"   Successfully read {len(content)} characters.")

            # Extract header section
            import re
            import uuid
            header_end = re.search(r'\[\d{2}:\d{2}:\d{2}\]', content)
            if header_end:
                header_text = content[:header_end.start()].strip()
                print(f"   📋 Extracted header section using timestamp pattern")
            else:
                lines = content.split('\n')
                header_text = '\n'.join(lines[:14])
                print(f"   📋 Extracted header section using first 14 lines fallback")

            # Create header chunk (special chunk type, not in parent-child hierarchy)
            header_chunk = {
                "chunk_id": str(uuid.uuid4()),
                "parent_id": None,
                "chunk_type": "header",
                "external_id": transcript_id,
                "text": header_text,
                "speaker_name": None,
                "start_time": 0.0,
                "end_time": 0.0,
                "sales_stage": None,
                "conversation_phase": None,
                "detected_topics": [],
                "intent": None,
                "sentiment": None,
                "discourse_marker": None,
                "contains_entity": False,
                "turn_count": None,
                "speaker_balance": None
            }

            # Create parent-child chunks from dialogue
            if structured_dialogue and len(structured_dialogue) > 0:
                print(f"   🧠 Creating parent-child chunks from {len(structured_dialogue)} speaker turns")

                # Use new parent-child chunker
                child_chunks, parent_chunks = self.semantic_chunker.chunk_dialogue(
                    structured_dialogue,
                    conversation_phases,
                    external_id=transcript_id
                )

                print(f"   ✅ Created {len(child_chunks)} child chunks (speaker turns)")
                print(f"   ✅ Created {len(parent_chunks)} parent chunks (phase segments)")

                # Combine all chunks for return
                all_chunks = [header_chunk] + parent_chunks + child_chunks

                return {
                    "all_chunks": all_chunks,  # For Baserow sync (all types)
                    "child_chunks": child_chunks,  # For Qdrant embedding
                    "parent_chunks": parent_chunks,  # For Qdrant payload storage
                    "header_chunk": header_chunk  # For Qdrant metadata
                }

            else:
                # No dialogue, return just header
                print(f"   ⚠️ No structured dialogue available")
                return {
                    "all_chunks": [header_chunk],
                    "child_chunks": [],
                    "parent_chunks": [],
                    "header_chunk": header_chunk
                }

        except FileNotFoundError:
            print(f"   ❌ ERROR: File not found at {file_path}")
            return {"all_chunks": [], "child_chunks": [], "parent_chunks": [], "header_chunk": None}
        except Exception as e:
            print(f"   ❌ ERROR: An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
            return {"all_chunks": [], "child_chunks": [], "parent_chunks": [], "header_chunk": None}


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
