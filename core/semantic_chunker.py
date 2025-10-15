"""
Semantic Dialogue Chunker - Parent-Child Architecture

Creates two-level chunking hierarchy:
1. CHILD CHUNKS: Individual speaker turns (embedded in vector DB)
   - Each speaker turn = 1 child chunk
   - Precise, focused embeddings for high-precision retrieval
   - Rich metadata (speaker, timestamp, intent, sentiment, topics)

2. PARENT CHUNKS: Conversation phase segments (stored, not embedded)
   - Groups 5-10 related speaker turns by conversation phase
   - Provides broader context when child chunk matches
   - Links to children via parent_id

Parent-Child Linking:
- Each child chunk has a parent_id UUID
- Parent chunks contain list of child_chunk_ids
- Retrieval: Find children via vector search, return parent context
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
import uuid


class SemanticDialogueChunker:
    """
    Creates parent-child chunk hierarchy from dialogue turns.

    Child chunks: Individual speaker turns (1 turn = 1 chunk)
    Parent chunks: Conversation phase segments (5-10 turns grouped)
    """

    def __init__(
        self,
        turns_per_parent: int = 7,  # Target turns per parent chunk (5-10 range)
        min_turns_per_parent: int = 5,  # Minimum turns before creating new parent
        max_turns_per_parent: int = 10  # Maximum turns before forcing new parent
    ):
        """
        Initialize parent-child chunker.

        Args:
            turns_per_parent: Target number of speaker turns per parent chunk
            min_turns_per_parent: Minimum turns for a parent chunk
            max_turns_per_parent: Maximum turns before forcing split
        """
        self.turns_per_parent = turns_per_parent
        self.min_turns_per_parent = min_turns_per_parent
        self.max_turns_per_parent = max_turns_per_parent

    def chunk_dialogue(
        self,
        structured_dialogue: List[Dict[str, Any]],
        conversation_phases: List[Dict[str, Any]] = None,
        external_id: str = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Create parent-child chunk hierarchy from dialogue turns.

        Strategy:
        1. Each speaker turn becomes a CHILD chunk (with UUID)
        2. Group 5-10 child chunks into PARENT chunks by conversation phase
        3. Link children to parents via parent_id
        4. Preserve all metadata (speaker, timestamp, intent, sentiment, topics)

        Args:
            structured_dialogue: List of enriched dialogue turns
            conversation_phases: List of conversation phase boundaries
            external_id: Transcript ID for linking chunks

        Returns:
            Tuple of (child_chunks, parent_chunks)
            - child_chunks: List of individual speaker turn chunks with parent_id
            - parent_chunks: List of conversation phase segment chunks with child_chunk_ids
        """
        if not structured_dialogue:
            return [], []

        # Step 1: Create child chunks (1 turn = 1 chunk)
        child_chunks = self._create_child_chunks(structured_dialogue, external_id)

        # Step 2: Group children into parents by conversation phase
        parent_chunks = self._create_parent_chunks(child_chunks, conversation_phases, external_id)

        # Step 3: Link children to parents
        self._link_children_to_parents(child_chunks, parent_chunks)

        return child_chunks, parent_chunks

    def _create_child_chunks(
        self,
        structured_dialogue: List[Dict[str, Any]],
        external_id: str
    ) -> List[Dict[str, Any]]:
        """
        Create child chunks: 1 speaker turn = 1 child chunk.

        Each child chunk is a complete speaker turn with:
        - Unique chunk_id (UUID)
        - Speaker metadata (name, timestamp)
        - Semantic metadata (intent, sentiment, topics)
        - Sales metadata (sales_stage, detected_topics)
        - parent_id (assigned later)
        """
        child_chunks = []

        for idx, turn in enumerate(structured_dialogue):
            # Generate unique chunk ID
            chunk_id = str(uuid.uuid4())

            # Extract timestamp in seconds (convert HH:MM:SS to seconds)
            timestamp_str = turn.get("timestamp", "00:00:00")
            start_time = self._timestamp_to_seconds(timestamp_str)

            # Estimate end time (next turn's start or +15 seconds)
            if idx + 1 < len(structured_dialogue):
                next_timestamp = structured_dialogue[idx + 1].get("timestamp", "00:00:00")
                end_time = self._timestamp_to_seconds(next_timestamp)
            else:
                end_time = start_time + 15.0  # Default 15 second turn

            # Detect topics from text (simple keyword extraction)
            detected_topics = self._extract_topics(turn.get("text", ""))

            # Map conversation_phase to sales_stage
            sales_stage = self._phase_to_sales_stage(turn.get("conversation_phase"))

            child_chunk = {
                "chunk_id": chunk_id,
                "parent_id": None,  # Assigned later
                "chunk_type": "child",
                "external_id": external_id,
                "text": turn.get("text", ""),
                "speaker_name": turn.get("speaker", "Unknown"),
                "start_time": start_time,
                "end_time": end_time,
                "sales_stage": sales_stage,
                "conversation_phase": turn.get("conversation_phase"),
                "detected_topics": detected_topics,
                "intent": turn.get("intent"),
                "sentiment": turn.get("sentiment"),
                "discourse_marker": turn.get("discourse_marker"),
                "contains_entity": turn.get("contains_entity", False),
                "timestamp": timestamp_str,  # Keep original format
                "turn_index": idx
            }

            child_chunks.append(child_chunk)

        return child_chunks

    def _create_parent_chunks(
        self,
        child_chunks: List[Dict[str, Any]],
        conversation_phases: List[Dict[str, Any]],
        external_id: str
    ) -> List[Dict[str, Any]]:
        """
        Create parent chunks by grouping 5-10 child chunks by conversation phase.

        Each parent chunk:
        - Groups children from same conversation phase
        - Contains aggregated text from all children
        - Has metadata: phase, timestamp range, turn count, speaker balance
        - Links to children via child_chunk_ids list
        """
        parent_chunks = []

        if conversation_phases and len(conversation_phases) > 0:
            # Group by conversation phase
            for phase in conversation_phases:
                phase_name = phase.get("phase")

                # Find all child chunks in this phase
                phase_children = [
                    c for c in child_chunks
                    if c.get("conversation_phase") == phase_name
                ]

                if not phase_children:
                    continue

                # Split large phases into multiple parents (5-10 turns each)
                parent_groups = self._group_children_into_parents(phase_children)

                for group in parent_groups:
                    parent_chunk = self._build_parent_from_children(group, external_id)
                    parent_chunks.append(parent_chunk)

        else:
            # No phases, group by turn count only
            parent_groups = self._group_children_into_parents(child_chunks)
            for group in parent_groups:
                parent_chunk = self._build_parent_from_children(group, external_id)
                parent_chunks.append(parent_chunk)

        return parent_chunks

    def _group_children_into_parents(
        self,
        children: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Group children into parent-sized groups (5-10 turns).
        """
        groups = []
        current_group = []

        for child in children:
            current_group.append(child)

            # Create new parent when we reach target size
            if len(current_group) >= self.turns_per_parent:
                groups.append(current_group)
                current_group = []

        # Add final group if not empty
        if current_group:
            # Merge with last group if too small
            if len(current_group) < self.min_turns_per_parent and groups:
                groups[-1].extend(current_group)
            else:
                groups.append(current_group)

        return groups

    def _build_parent_from_children(
        self,
        children: List[Dict[str, Any]],
        external_id: str
    ) -> Dict[str, Any]:
        """
        Build parent chunk from group of children.
        """
        parent_id = str(uuid.uuid4())

        # Aggregate text from all children
        texts = [c["text"] for c in children]
        parent_text = "\n".join([
            f"[{c['timestamp']}] {c['speaker_name']}: {c['text']}"
            for c in children
        ])

        # Aggregate metadata
        timestamps = [c["timestamp"] for c in children]
        speakers = [c["speaker_name"] for c in children]
        unique_speakers = list(set(speakers))

        # Speaker balance
        client_keywords = ["client", "iphone", "caller"]
        client_turns = sum(1 for s in speakers if any(kw in s.lower() for kw in client_keywords))
        speaker_balance = round(client_turns / len(speakers), 2) if speakers else 0.5

        # Most common phase
        phases = [c.get("conversation_phase") for c in children if c.get("conversation_phase")]
        conversation_phase = max(set(phases), key=phases.count) if phases else None

        # Sales stage
        sales_stage = self._phase_to_sales_stage(conversation_phase)

        # Aggregate topics
        all_topics = []
        for c in children:
            topics = c.get("detected_topics", [])
            if isinstance(topics, list):
                all_topics.extend(topics)
        detected_topics = list(set(all_topics))[:10]  # Top 10 unique topics

        return {
            "chunk_id": parent_id,
            "parent_id": None,  # Parents have no parent
            "chunk_type": "parent",
            "external_id": external_id,
            "text": parent_text,
            "conversation_phase": conversation_phase,
            "sales_stage": sales_stage,
            "detected_topics": detected_topics,
            "timestamp_start": timestamps[0] if timestamps else None,
            "timestamp_end": timestamps[-1] if timestamps else None,
            "start_time": children[0]["start_time"],
            "end_time": children[-1]["end_time"],
            "turn_count": len(children),
            "speaker_balance": speaker_balance,
            "speakers": unique_speakers,
            "child_chunk_ids": [c["chunk_id"] for c in children]
        }

    def _link_children_to_parents(
        self,
        child_chunks: List[Dict[str, Any]],
        parent_chunks: List[Dict[str, Any]]
    ):
        """
        Link each child to its parent by setting parent_id.
        """
        # Build mapping: child_id -> parent_id
        child_to_parent = {}
        for parent in parent_chunks:
            parent_id = parent["chunk_id"]
            for child_id in parent["child_chunk_ids"]:
                child_to_parent[child_id] = parent_id

        # Update children with parent_id
        for child in child_chunks:
            child_id = child["chunk_id"]
            child["parent_id"] = child_to_parent.get(child_id)

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert HH:MM:SS timestamp to seconds."""
        try:
            parts = timestamp.split(":")
            if len(parts) == 3:
                h, m, s = parts
                return float(h) * 3600 + float(m) * 60 + float(s)
            return 0.0
        except:
            return 0.0

    def _extract_topics(self, text: str) -> List[str]:
        """
        Simple topic extraction using keyword matching.
        Returns list of detected topics/keywords.
        """
        # Estate planning keywords
        keywords = {
            "estate planning", "trust", "will", "power of attorney",
            "healthcare directive", "beneficiary", "executor", "trustee",
            "probate", "asset protection", "tax planning", "inheritance",
            "revocable", "irrevocable", "living trust", "testamentary",
            "guardianship", "conservatorship", "real estate", "property",
            "children", "spouse", "family", "divorce", "marriage",
            "business", "LLC", "corporation", "partnership",
            "retirement", "IRA", "401k", "pension", "investment",
            "debt", "creditor", "lawsuit", "medicaid", "nursing home",
            "price", "cost", "fee", "payment", "deposit", "financing"
        }

        text_lower = text.lower()
        detected = []

        for keyword in keywords:
            if keyword in text_lower:
                detected.append(keyword)

        return detected[:5]  # Return top 5 topics

    def _phase_to_sales_stage(self, conversation_phase: Optional[str]) -> str:
        """
        Map conversation phase to Baserow sales_stage values.

        Baserow sales_stage options:
        - Setting up for meeting
        - Assistant Intro Rep
        - Greeting
        - Client Motivation
        - Set Meeting Agenda
        - Establish Credibility
        - Discovery
        - Compare Options
        - Present Solution
        - Pricing
        - Objection Handling
        - Closing
        - Unknown
        """
        if not conversation_phase:
            return "Unknown"

        phase_lower = conversation_phase.lower()

        # Exact matches first
        if "setting up" in phase_lower or "pre-meeting" in phase_lower:
            return "Setting up for meeting"
        if "assistant intro" in phase_lower or "rep intro" in phase_lower:
            return "Assistant Intro Rep"
        if "greeting" in phase_lower or "hello" in phase_lower or "introduction" in phase_lower:
            return "Greeting"
        if "motivation" in phase_lower or "why" in phase_lower:
            return "Client Motivation"
        if "agenda" in phase_lower or "plan" in phase_lower:
            return "Set Meeting Agenda"
        if "credibility" in phase_lower or "about us" in phase_lower or "experience" in phase_lower:
            return "Establish Credibility"
        if "discovery" in phase_lower or "needs" in phase_lower or "goals" in phase_lower or "estate details" in phase_lower:
            return "Discovery"
        if "compare" in phase_lower or "options" in phase_lower or "competition" in phase_lower:
            return "Compare Options"
        if "present" in phase_lower or "solution" in phase_lower or "structure" in phase_lower or "benefits" in phase_lower:
            return "Present Solution"
        if "pric" in phase_lower or "cost" in phase_lower or "fee" in phase_lower or "money" in phase_lower:
            return "Pricing"
        if "objection" in phase_lower or "rebuttal" in phase_lower or "concern" in phase_lower:
            return "Objection Handling"
        if "closing" in phase_lower or "close" in phase_lower or "ending" in phase_lower or "scheduling" in phase_lower:
            return "Closing"

        return "Unknown"
