"""
Semantic Dialogue Chunker

Dialogue-turn-aware semantic chunking that respects:
1. Dialogue turn boundaries (never split within a turn)
2. Semantic coherence (group related Q&A exchanges)
3. Conversation phase boundaries (natural topic shifts)
4. Entity preservation (never split entities across chunks)
5. Optimal overlap (1-2 dialogue turns for context preservation)

Best Practices:
- Chunks represent complete semantic units (Q&A pairs, topic segments)
- 10-20% overlap at turn level (not character level)
- Preserve NER metadata within chunks
- Use conversation phases as natural split points
"""

from typing import List, Dict, Any, Optional
from collections import Counter


class SemanticDialogueChunker:
    """
    Creates semantically coherent chunks from dialogue turns.
    Respects conversation structure and never splits mid-turn or mid-entity.
    """

    def __init__(
        self,
        target_chunk_size: int = 1400,  # Target characters per chunk
        min_chunk_size: int = 700,      # Minimum chunk size (50% of target)
        max_chunk_size: int = 2100,     # Maximum chunk size (150% of target)
        overlap_turns: int = 2          # Number of turns to overlap between chunks
    ):
        """
        Initialize semantic dialogue chunker.

        Args:
            target_chunk_size: Target chunk size in characters (~350 tokens)
            min_chunk_size: Minimum acceptable chunk size
            max_chunk_size: Maximum chunk size before forced split
            overlap_turns: Number of dialogue turns to overlap (for context)
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_turns = overlap_turns

    def chunk_dialogue(
        self,
        structured_dialogue: List[Dict[str, Any]],
        conversation_phases: List[Dict[str, Any]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Chunk dialogue turns into semantically coherent segments.

        Strategy:
        1. Use conversation phases as primary split points
        2. Within phases, create chunks of ~target_chunk_size characters
        3. Respect dialogue turn boundaries (never split a turn)
        4. Add overlap_turns from previous chunk for context
        5. Preserve all metadata (phase, intent, sentiment, entities)

        Args:
            structured_dialogue: List of enriched dialogue turns
            conversation_phases: List of conversation phase boundaries

        Returns:
            List of chunk lists (each chunk is a list of dialogue turns)
        """
        if not structured_dialogue:
            return []

        chunks = []

        if conversation_phases and len(conversation_phases) > 1:
            # Strategy 1: Phase-based chunking (natural topic boundaries)
            chunks = self._chunk_by_phases(structured_dialogue, conversation_phases)
        else:
            # Strategy 2: Size-based chunking (no clear phases)
            chunks = self._chunk_by_size(structured_dialogue)

        # Add overlap between chunks
        chunks_with_overlap = self._add_overlap(chunks)

        return chunks_with_overlap

    def _chunk_by_phases(
        self,
        dialogue: List[Dict[str, Any]],
        phases: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Chunk dialogue using conversation phase boundaries.
        Each phase becomes one or more chunks.
        """
        chunks = []

        # Group turns by phase
        for phase in phases:
            phase_name = phase.get("phase")
            phase_start = phase.get("start_timestamp")
            phase_end = phase.get("end_timestamp")

            # Find turns in this phase
            phase_turns = []
            for turn in dialogue:
                turn_time = turn.get("timestamp")
                turn_phase = turn.get("conversation_phase")

                # Match by phase name or timestamp range
                if turn_phase == phase_name or (
                    phase_start and phase_end and
                    phase_start <= turn_time <= phase_end
                ):
                    phase_turns.append(turn)

            # If phase is too large, split it
            if phase_turns:
                phase_chunks = self._split_large_phase(phase_turns)
                chunks.extend(phase_chunks)

        # Handle turns not assigned to any phase
        unassigned_turns = [t for t in dialogue if t.get("conversation_phase") is None]
        if unassigned_turns:
            unassigned_chunks = self._chunk_by_size(unassigned_turns)
            chunks.extend(unassigned_chunks)

        return chunks

    def _split_large_phase(self, turns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Split a large conversation phase into multiple chunks if needed.
        """
        total_chars = sum(len(t.get("text", "")) for t in turns)

        if total_chars <= self.max_chunk_size:
            # Phase fits in one chunk
            return [turns]

        # Phase is too large, split by size
        return self._chunk_by_size(turns)

    def _chunk_by_size(self, turns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Create chunks based on target size, respecting turn boundaries.
        """
        chunks = []
        current_chunk = []
        current_size = 0

        for turn in turns:
            turn_text = turn.get("text", "")
            turn_size = len(turn_text)

            # Check if adding this turn exceeds max size
            if current_size + turn_size > self.max_chunk_size and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 0

            # Add turn to current chunk
            current_chunk.append(turn)
            current_size += turn_size

            # Check if we've reached target size (soft limit)
            if current_size >= self.target_chunk_size and current_size <= self.max_chunk_size:
                # Check if next turn would push us over max
                # If so, end chunk here
                next_turn_size = len(turns[turns.index(turn) + 1].get("text", "")) if turns.index(turn) + 1 < len(turns) else 0
                if current_size + next_turn_size > self.max_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0

        # Add final chunk if not empty
        if current_chunk:
            # Only add if it meets minimum size OR it's the only chunk
            if current_size >= self.min_chunk_size or len(chunks) == 0:
                chunks.append(current_chunk)
            else:
                # Too small, merge with previous chunk
                if chunks:
                    chunks[-1].extend(current_chunk)

        return chunks

    def _add_overlap(self, chunks: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """
        Add overlap between chunks for context preservation.
        Includes last N turns from previous chunk at start of next chunk.
        """
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = [chunks[0]]  # First chunk has no overlap

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]

            # Get last N turns from previous chunk
            overlap_turns = prev_chunk[-self.overlap_turns:] if len(prev_chunk) >= self.overlap_turns else prev_chunk

            # Prepend overlap to current chunk
            overlapped_chunk = overlap_turns + current_chunk
            overlapped_chunks.append(overlapped_chunk)

        return overlapped_chunks

    def turns_to_text(self, turns: List[Dict[str, Any]], format: str = "dialogue") -> str:
        """
        Convert dialogue turns to formatted text.

        Args:
            turns: List of dialogue turn dictionaries
            format: "dialogue" (timestamped) or "plain" (text only)

        Returns:
            Formatted text string
        """
        if format == "dialogue":
            # Format: [HH:MM:SS] Speaker: Text
            lines = []
            for turn in turns:
                timestamp = turn.get("timestamp", "00:00:00")
                speaker = turn.get("speaker", "Unknown")
                text = turn.get("text", "")
                lines.append(f"[{timestamp}] {speaker}: {text}")
            return "\n".join(lines)
        else:
            # Plain text
            return " ".join(turn.get("text", "") for turn in turns)

    def compute_chunk_metadata(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute metadata for a chunk from its constituent turns.

        Returns rich metadata for storage in vector DB:
        - Conversation phase (most common)
        - Speakers and speaker balance
        - Timestamp range
        - Semantic NLP metadata (intent, sentiment)
        - Entity presence
        - Turn count
        - Question/objection indicators
        """
        if not turns:
            return {}

        # Basic metadata
        timestamps = [t.get("timestamp") for t in turns if t.get("timestamp")]
        speakers = [t.get("speaker") for t in turns if t.get("speaker")]
        phases = [t.get("conversation_phase") for t in turns if t.get("conversation_phase")]

        # Conversation phase (most common)
        phase = max(set(phases), key=phases.count) if phases else None

        # Speakers
        unique_speakers = list(set(speakers))
        speaker_counts = Counter(speakers)

        # Speaker balance (ratio of client to rep turns)
        client_keywords = ["client", "iphone", "caller"]  # Common client identifiers
        client_turns = sum(1 for s in speakers if any(kw in s.lower() for kw in client_keywords))
        speaker_balance = client_turns / len(speakers) if speakers else 0.5

        # Semantic NLP metadata
        intents = [t.get("intent") for t in turns if t.get("intent")]
        sentiments = [t.get("sentiment") for t in turns if t.get("sentiment")]
        discourse_markers = [t.get("discourse_marker") for t in turns if t.get("discourse_marker") and t.get("discourse_marker") != "none"]

        dominant_intent = max(set(intents), key=intents.count) if intents else None
        dominant_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else None

        # Entity presence
        contains_entities = any(t.get("contains_entity") for t in turns)

        # Question/objection indicators
        question_count = sum(1 for i in intents if i == "question")
        objection_count = sum(1 for i in intents if i == "objection")

        return {
            "conversation_phase": phase,
            "speakers": unique_speakers,
            "speaker_balance": round(speaker_balance, 2),
            "timestamp_start": timestamps[0] if timestamps else None,
            "timestamp_end": timestamps[-1] if timestamps else None,
            "turn_count": len(turns),
            "dominant_intent": dominant_intent,
            "dominant_sentiment": dominant_sentiment,
            "contains_entities": contains_entities,
            "discourse_markers": list(set(discourse_markers)),
            "question_count": question_count,
            "objection_count": objection_count,
            "has_objections": objection_count > 0
        }
